from typing import List

from intent2.projection import project_pos

from intent2.alignment import heuristic_alignment
from sklearn.linear_model import LogisticRegression
from sklearn.base import TransformerMixin
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import CountVectorizer

from collections import defaultdict

from spacy.tokens import Doc, Token

from .model import GlossWord, Instance
import pickle

class LRWrapper(object):
    """
    Class to wrap the regression model itself
    and the vectorizer used to transform features
    into the same serializable object.
    """
    def __init__(self, lr: LogisticRegression, vectorizer: DictVectorizer, vocab: dict=None):
        self.model = lr
        self.vectorizer = vectorizer
        self.vocab = vocab

    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path):
        """:rtype: LRWrapper"""
        with open(path, 'rb') as f:
            return pickle.load(f)

    def classify(self, word_tokens: List[GlossWord],
                 projected_tags: bool=False, subword_tags: bool=False,
                 use_vocab: bool = True):
        """
        Given a list of gloss words, extract features and
        """
        vectors = [extract_gloss_word_feats(gw, self.vocab,
                                            projected_tag=gw.pos if projected_tags else None,
                                            subword_tags=[gsw.pos for gsw in gw.subwords if gsw.pos] if subword_tags else [],
                                            use_vocab=use_vocab)
                   for gw in word_tokens]
        X = self.vectorizer.transform(vectors)
        predictions = self.model.predict(X)
        return predictions

def proj_classify_backoff(inst: Instance, classifier: LRWrapper):
    if inst.gloss:
        class_tags = classifier.classify(inst.gloss)

        if inst.trans:
            heuristic_alignment(inst)
            if inst.trans.alignments:
                project_pos(inst)



def dummy_tok(x):
    """
    Dummy tokenizer that just returns the token unprocessed.
    """
    return x

class PreTokenizedCountVectorizer(CountVectorizer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, tokenizer=dummy_tok, preprocessor=dummy_tok)


def extract_gloss_word_feats(gloss_w: GlossWord, vocab: dict,
                             projected_tag: str = None,
                             subword_tags: List[str] = None,
                             use_vocab: bool = True):
    """
    Given a gloss word, return the feature vector
    for classification.
    """
    X_word = defaultdict(float)

    from .processing import load_spacy
    en = load_spacy()
    d = en([text for index, text in gloss_w.subword_parts])

    # If the subword_parts is empty, just use the literal
    # word as the one feature (it should be PUNC)
    if len(d) == 0:
        X_word[gloss_w.string] = 1.0
        return X_word

    # Normalize the amount each subword contributes
    amount = 1/len(d)

    # -------------------------------------------
    # Add the projected tag if provided
    # -------------------------------------------
    if projected_tag:
        X_word['_projected_pos_{}'.format(projected_tag)] += 1.0

    if subword_tags:
        for subword_tag in subword_tags:
            X_word['_projected_sw_pos_{}_'.format(subword_tag)] += amount

    # -------------------------------------------
    # Extract features from the subwords
    # -------------------------------------------


    for subword_token in d: # type: Token
        lower_subword = subword_token.text.lower()
        lemma = subword_token.lemma_ if subword_token.pos_ is not 'PUNCT' else None
        if lemma and lemma != lower_subword:
            X_word['_lemma_{}'.format(lemma)] += amount

        # If a vocab-to-tag mapping is provided,
        # use it add probabilities for this word.
        if use_vocab:
            if subword_token.text in vocab:
                for tag in vocab[subword_token.text]:
                    X_word['_vocab_pos_{}'.format(tag)] += vocab[subword_token.text][tag] * amount

            # A feature indicating that part of this
            # token is OOV might be helpful (for things like PROPN)
            else:
                X_word['_vocab_oov_'] += amount

        # If the lemma is the same as the word, add
        # the lemma, otherwise add both.
        if lemma == lower_subword:
            X_word[lower_subword] += amount

    return X_word

def describe_logreg(model: LogisticRegression,
                    vectorizer: DictVectorizer,
                    n: int=10):
    """
    Given a logistic regression model, print out the categories
    and the highest rated features.

    :param n: The number of top-weighted features to print out for each category.
    """
    # Keep a dictionary to track the feature/coefficients
    # by category so they can be ranked and printed out later.
    interpretation_dict = defaultdict(dict)
    feat_names = vectorizer.get_feature_names() if vectorizer else range(len(model.coef_))

    for class_, coefficients in zip(model.classes_, model.coef_):
        for feat_name, coefficient in zip(feat_names, coefficients):
            interpretation_dict[class_][feat_name] = coefficient

    # Now iterate through each category and print out the top_n highest-weighted
    # feats.
    for cat in interpretation_dict:
        print(cat)
        sorted_feats = sorted(interpretation_dict[cat].items(), key=lambda x: x[1], reverse=True)
        for feat, coef in sorted_feats[:n]:
            print('{:10} {:20} {:.5f}'.format('', feat, coef))