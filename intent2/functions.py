"""
This file is to be used for the main
tricky code implementations of INTENT,
namely:

    * Projecting annotation
    * Performing alignment

"""
from intent2.model import Instance, Word, SubWord, Phrase
from intent2.processing import process_trans_if_needed
from typing import Iterable, Generator, List, Tuple

from spacy.tokens import Doc, Span, Token
import logging

ENRICH_LOG = logging.getLogger('enrich')

# -------------------------------------------
# Dependency Parsing
# -------------------------------------------
from nltk.tree import ParentedTree
class DependencyTree(ParentedTree):

    def __init__(self, node, children=None, label=None):
        """
        :param node: The word
        :param children: children trees
        :type children: List[Union[DependencyTree,None]]
        :param label:
        """
        self.type = label # The relation of this node to its parent
        super().__init__(node, children)



def extract_ds(p: Phrase):
    """
    Given a phrase that's been assigned a dependency analysis,
    extract it as a tree that can be manipulated and traversed.
    """
    dep_links = p.dependencies
    from nltk.tree import ParentedTree

def project_dependencies(inst: Instance):
    pass


# -------------------------------------------
# POS Projection
# -------------------------------------------

# NOUN > VERB > ADJ > ADV > PRON > DET > ADP > CONJ > PRT > NUM > PUNC > X
precedence = ['PROPN', 'NOUN','VERB', 'ADJ', 'ADV', 'PRON', 'DET', 'ADP', 'CONJ', 'PRT', 'NUM', 'PUNC', 'X']

def project_pos(inst: Instance):
    """
    Project part-of-speech tags using the bilingual alignment.
    """
    ENRICH_LOG.info('Projecting part-of-speech tags.')

    # There must be alignments present to project
    assert inst.trans.alignments
    process_trans_if_needed(inst)

    # Now, iterate over the translation words, and project their
    for trans_w in inst.trans:
        for aligned_gloss in trans_w.alignments: # type: SubWord

            # Check to see if the aligned gloss already has
            # a part-of-speech tag, or if it does have one, that
            # it is a lower precedent than the proposed aligned tag.
            if (not aligned_gloss.pos or
                precedence.index(aligned_gloss.pos) > precedence.index(trans_w.pos)):
                aligned_gloss.pos = trans_w.pos

    combine_subword_tags(inst.gloss)

def combine_subword_tags(p: Phrase):
    """
    Take a pass over a  phrase, and combine
    the subword-level part-of-speech tags
    """
    for word in p:
        tags = [subword.pos for subword in word if subword.pos]
        best_tags = sorted(tags, key=lambda tag: precedence.index(tag))
        word.pos = best_tags[0] if best_tags else None

# -------------------------------------------
# Dependency Projection
# -------------------------------------------
