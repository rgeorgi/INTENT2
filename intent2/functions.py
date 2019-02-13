"""
This file is to be used for the main
tricky code implementations of INTENT,
namely:

    * Projecting annotation
    * Performing alignment

"""
from intent2.model import Instance, Word, SubWord, Phrase, DependencyLink
from intent2.processing import process_trans_if_needed
from typing import Iterable, Generator, List, Tuple, Iterator

from spacy.tokens import Doc, Span, Token
import logging

from intent2.utils.visualization import visualize_alignment

ENRICH_LOG = logging.getLogger('enrich')


# -------------------------------------------
# Dependency Parsing
# -------------------------------------------
class DependencySet(set):
    """
    Rather than representing a dependency structure
    as a tree, just keep it as a set of links between
    items.
    """
    def __new__(cls, iterable: Iterable=None, root: DependencyLink=None):
        if iterable is None:
            iterable = []
        ds = cls(iterable)

# -------------------------------------------
# Dependency Projection
# -------------------------------------------

DS_PROJ_LOG = logging.getLogger('ds_project')

def project_ds(inst: Instance):
    """
    1. Our DS projection algorithm is similar to the projection algorithms
        described in (Hwa et al. 2002) and (Quirk et al. 2005).

        It has four steps:

            1. Copy the English DS. and remove all the unaligned English words
            from the DS.

            2. We replace each English word in the DS with the corresponding
            source words. If an English word x aligns to several source words,
            we will make several copies of the node for x, one copy for each
            such source word. The copies will all be siblings in the DS.
            If a source word aligns to multiple English words, after Step 2
            the source word will have several copies in the resulting DS.

            3. In the third step, we keep only the copy that is closest
            to the root and remove all the other copies.

            4. In Step 4, we attach unaligned source words to the DS
            using the heuristics described in (Quirk et al. 2005).
    """
    # -- 0) Start by ensuring the translation line has a ds.
    process_trans_if_needed(inst)

    trans_ds = inst.trans.dependency_structure

    print(visualize_alignment(inst))
    print(trans_ds.visualize(inst.trans))

    for trans_word in inst.trans:
        if not trans_word.alignments:
            trans_ds.remove_word(trans_word)

    print(trans_ds.visualize(inst.trans))


    sys.exit()

    # -- 1) Remove all unaligned words. Do this by looking at all of the
    DS_PROJ_LOG.debug('Removing unaligned words from instance "{}"'.format(inst.id))
    unaligned_words = {trans_word for trans_word in inst.trans if not trans_word.alignments}
    for trans_word in inst.trans:
        if not trans_word.alignments:
            new_links = set()
            for dependency_link in trans_word.dependency_structure:
                new_links |= dependency_link.promote()
            print(trans_word.dependency_structure, new_links)




# -------------------------------------------
# POS Projection
# -------------------------------------------

# NOUN > VERB > ADJ > ADV > PRON > DET > ADP > CONJ > PRT > NUM > PUNC > X
precedence = ['PROPN', 'NOUN','VERB', 'ADJ', 'ADV', 'PRON', 'DET', 'ADP', 'CONJ', 'CCONJ', 'PART', 'NUM', 'PUNC', 'X', 'INTJ']

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



