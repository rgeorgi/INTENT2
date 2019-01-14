"""
This file is to be used for the main
tricky code implementations of INTENT,
namely:

    * Projecting annotation
    * Performing alignment

"""
from intent2.model import Instance
import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span, Token

def process_trans(inst, tag=True, parse=True):
    """
    Apply the SpaCy pipeline to the translation sentence.

    :type inst: Instance
    """
    # Parsing requires a translation line
    assert inst.trans

    spacy_eng = spacy.load('en_core_web_sm') # type: Language

    doc = spacy_eng.tokenizer.tokens_from_list([w.hyphenated for w in inst.trans])

    spacy_eng.tagger(doc)
    spacy_eng.parser(doc)

    # Now let's go through the words, and assign attributes to them.
    assert len(inst.trans) == len(doc)
    for i in range(len(inst.trans)):
        trans_word = inst.trans[i]
        spacy_word = doc[i]

        # Add POS Tag
        if tag:
            trans_word.pos = spacy_word.pos_

        # Add Dependency Head
        if parse:
            if spacy_word.head.i != i:
                trans_word.add_head(inst.trans[spacy_word.head.i])
            # If spacy says that a word is its own head,
            # it is the root.
            else:
                inst.trans.root = trans_word

    print(sorted(inst.trans.dependencies, key=lambda x: x.parent.index))





def heuristic_alignment(inst):
    """
    Implement the alignment between words

    :type inst: Instance
    """

    # To do heuristic alignment, we need minimally a gloss and translation line.
    assert inst.gloss and inst.trans

    for trans_word in inst.trans:
        print(trans_word)
    for gloss_word in inst.gloss:
        for gloss_part in gloss_word:
            # Split the glosses on periods for heuristic alignment purposes
            print(gloss_part.hyphenated.split('.'))