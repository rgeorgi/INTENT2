"""
Module to do things like dependency parsing and
part-of-speech-tagging
"""
from collections import Iterable

from intent2.exceptions import ProcessException
from intent2.model import Instance, DependencyStructure, DependencyLink

import spacy
from spacy.tokenizer import Tokenizer
from spacy.language import Language
from spacy.tokens import Doc

# -------------------------------------------
# Set up logging
# -------------------------------------------
import logging
PROCESS_LOG = logging.getLogger()

# -------------------------------------------
# Set up spaCy
# -------------------------------------------
global SPACY_ENG # type: Language
SPACY_ENG = None

class DummyTokenizer(Tokenizer):
    """
    Class for initializing spaCy, but taking pre-tokenized
    lists instead of strings.
    """
    def __call__(self, input: Iterable, **kwargs):
        d = Doc(self.vocab, words=input)
        return d


def load_spacy():
    """
    Lazy-load the spacy model when needed.
    :return:
    """
    global SPACY_ENG
    if SPACY_ENG is None:
        PROCESS_LOG.info('spaCy model was not previously loaded. Now loading...')
        SPACY_ENG = spacy.load('en_core_web_lg')  # type: Language
        SPACY_ENG.tokenizer = DummyTokenizer(SPACY_ENG.vocab)
    return SPACY_ENG

# -------------------------------------------
# Processing for different lines
# -------------------------------------------

def process_trans(inst: Instance, tag=True, parse=True):
    """
    Apply the SpaCy pipeline to the translation sentence.

    :type inst: Instance
    """
    # Parsing requires a translation line
    if not inst.trans:
        raise ProcessException("No translation line present, cannot process.")

    spacy_eng = load_spacy()

    trans_doc = Doc(spacy_eng.vocab, words=[w.string for w in inst.trans])

    # Tag and parse
    PROCESS_LOG.info('Tagging and parsing translation line "{}"'.format(inst.trans.hyphenated))
    spacy_eng.tagger(trans_doc)
    spacy_eng.parser(trans_doc)

    # Now let's go through the words, and assign attributes to them.
    assert len(inst.trans) == len(trans_doc)

    trans_ds = DependencyStructure()

    for i in range(len(inst.trans)):
        trans_word = inst.trans[i]
        spacy_word = trans_doc[i] # type: Token

        # Add POS Tag
        if tag:
            trans_word.pos = spacy_word.pos_

        # Add Dependency Head
        if parse:
            if spacy_word.head.i != i:
                trans_ds.add(DependencyLink(child=trans_word,
                                            parent=inst.trans[spacy_word.head.i],
                                            link_type=spacy_word.dep_))

            # If spacy says that a word is its own head,
            # it is the root.
            else:
                trans_ds.add(DependencyLink(child=trans_word,
                                            parent=None,
                                            link_type='root'))

        # Add vector
        trans_word.spacy_token = spacy_word

        # Add lemmatization
        assert len(trans_word.subwords) == 1
        trans_word[0].lemma = spacy_word.lemma_
        # TODO: Should there be a case where a translation word has more than one subword?

    inst.trans.dependency_structure = trans_ds
    setattr(inst.trans, '_processed', True)




def process_trans_if_needed(inst: Instance):
    if not hasattr(inst.trans, '_processed'):
        process_trans(inst)
