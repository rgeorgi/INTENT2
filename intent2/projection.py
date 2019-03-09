"""
This file is to be used for the main
tricky code implementations of INTENT,
namely:

    * Projecting annotation
    * Performing alignment

"""
from intent2.model import Instance, Word, SubWord, Phrase, DependencyLink, TransWord
from intent2.processing import process_trans_if_needed
from typing import Iterable, Generator, List, Tuple, Iterator, Union
import itertools

from spacy.tokens import Doc, Span, Token
import logging

from intent2.utils.visualization import visualize_alignment

ENRICH_LOG = logging.getLogger('enrich')


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

    # -- 1) Get the dependency structure, anc create a copy.
    new_ds = inst.trans.dependency_structure.copy()
    for trans_word in [tw for tw in inst.trans if not tw.alignments]:
        new_ds.remove_word(trans_word)

    # -- 2) Replace all aligned words.
    for trans_word in [tw for tw in inst.trans if tw.alignments]: # type: TransWord

        # Iterate over the lang words for multiple alignment handling
        lang_words = trans_word.aligned_lang_words
        for lang_word in lang_words:
            new_ds.replace_word(trans_word, lang_word, remove=False)
        new_ds.remove_word(trans_word, promote=False)

    # Take stock of what words are aligned and unaligned at this point.
    aligned_lang_words = [w for w in inst.lang if w in new_ds.words]
    unaligned_lang_words = {w for w in inst.lang if w not in new_ds.words}
    assert set(aligned_lang_words) & unaligned_lang_words == set([])

    # -- 3) Look for duplicate LangWords, and only keep the shallowest copy.
    for word in aligned_lang_words:

        # Get the depth of the word in the tree (minimum number
        # of links traversed to make it to a root)
        parent_links = list(new_ds.get_parent_links(word))
        min_depth = min([new_ds.depth(parent_link) for parent_link in parent_links]) if parent_links else None

        # Remove all the links that have a depth less than the min_depth.
        # TODO: What about the case when multiple copies are at the same depth?
        for parent_link in parent_links:
            if new_ds.depth(parent_link) > min_depth:
                new_ds.remove(parent_link)

    # -- 4) Reattach unaligned words.
    #       Unaligned attachment from Quirk, et. al, 2005:
    #
    #          Unaligned target words are attached into the dependency
    #          structure as follows: assume there is an unaligned word
    #          t_j in position j. Let i < j and k > j be the target positions
    #          closest to j such that t_i depends on t_k or vice versa:
    #          attach t_j to the lower of t_i or t_k.
    #
    #          If all the nodes to the left (or right) of position j are
    #          unaligned, attach tj to the left-most (or right-most)
    #          word that is aligned.

    # We can't reattach unaligned words if no words were attached.
    if not aligned_lang_words:
        DS_PROJ_LOG.warning('No words were aligned for instance "{}". DS Projection aborted.'.format(inst.id))
        return

    links_to_add = set([])

    # TODO: Also need to consider the case where there is a word to the left and a word to the right…
    #       …but they are both aligned to ROOT.
    for unaligned_lang_word in unaligned_lang_words: # type: Word
        search_str = '{} ({})'.format(unaligned_lang_word.string, unaligned_lang_word.id)
        DS_PROJ_LOG.debug('Searching to reattach unaligned lang word: "{}"'.format(search_str))

        word_index = unaligned_lang_word.index
        closest_aligned_left_words = [lw for lw in aligned_lang_words if lw.index < word_index]
        closest_aligned_left_words.reverse()  # Reverse this so the first element is the closest
        closest_aligned_right_words = [rw for rw in aligned_lang_words if rw.index > word_index]

        # If no words are aligned to the right, attach to the closest word on the left.
        # If no words are aligned to the left, attach to the closest word on the right.
        if not closest_aligned_right_words and closest_aligned_left_words:
            closest_left_word = closest_aligned_left_words[0]
            links_to_add.add(DependencyLink(child=unaligned_lang_word, parent=closest_left_word))
            DS_PROJ_LOG.debug('No aligned words to the right of {} found, attaching to {}'.format(search_str, closest_left_word.id))
            continue
        if not closest_aligned_left_words and closest_aligned_right_words:
            links_to_add.add(DependencyLink(child=unaligned_lang_word, parent=closest_aligned_right_words[0]))
            DS_PROJ_LOG.debug('No aligned words to the right of {} found, attaching to {}'.format(search_str, closest_aligned_right_words[0].id))
            continue

        assert (closest_aligned_right_words or closest_aligned_left_words)


        # If there are words attached to both the left and right, iterate
        # through to find the closest pair that depend on each other,
        # and attach to the lower of the pair.

        # First, let's come up with the permutations to test, in order of increasing distance
        # from this index.
        word_pairs = list(itertools.product(closest_aligned_left_words, closest_aligned_right_words))

        # Sort the word pairs in order of increasing window size away from this word.
        word_pairs.sort(key = lambda pair: abs(word_index-pair[0].index) + abs(word_index-pair[1].index))

        make_attach_link = None
        for left_word, right_word in word_pairs:
            # If the right_word dominates the left_word... attach to the left_word
            if right_word in {link.parent for link in new_ds.get_parent_links(left_word)}:
                make_attach_link = DependencyLink(child=unaligned_lang_word, parent=right_word)
                break
            # Else, if the left word dominates the right_word... attach right_word
            elif left_word in {link.child for link in new_ds.get_parent_links(right_word)}:
                make_attach_link = DependencyLink(child=unaligned_lang_word, parent=left_word)
                break

        if make_attach_link is not None:
            links_to_add.add(make_attach_link)
            DS_PROJ_LOG.info('Reattaching unaligned word {} to {}'.format(search_str, make_attach_link.parent.id))
        else:
            DS_PROJ_LOG.info('No attachment site was found for lang word "{}"'.format(unaligned_lang_word.id))
            DS_PROJ_LOG.info('Options were: {}'.format(word_pairs))

    for link in links_to_add:
        new_ds.add(link)

    # Add the dependency structure to the language line.
    inst.lang.dependency_structure = new_ds
    return new_ds


# -------------------------------------------
# POS Projection
# -------------------------------------------

# NOUN > VERB > ADJ > ADV > PRON > DET > ADP > CONJ > PRT > NUM > PUNC > X
precedence = ['PROPN', 'NOUN','VERB', 'ADJ', 'ADV', 'PRON', 'DET', 'ADP', 'CONJ', 'CCONJ', 'PART', 'PRT', 'NUM', 'PUNC', 'X', 'SYM', 'INTJ', 'PUNCT']

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
# Clearing Bilingual Alignments/POS to do re-enrichment
# -------------------------------------------
def clear_bilingual_alignments(inst: Instance):
    """
    Remove bilingual alignments from an instance (not lang-to-gloss)
    """
    for trans_word in inst.trans:
        for aligned_item in list(trans_word.alignments): # type: Union[Word, SubWord]
            trans_word.remove_alignment(aligned_item)

def clear_pos_tags(p: Phrase):
    for word in p:
        word.pos = None
        for subword in word.subwords:
            subword.pos = None

def clear_all_pos_tags(inst: Instance):
    """
    Remove all POS tags from an instance
    """
    clear_pos_tags(inst.lang)
    clear_pos_tags(inst.gloss)
    clear_pos_tags(inst.trans)

# -------------------------------------------
# UnitTests
# -------------------------------------------
from unittest import TestCase

class DSProjectionTests(TestCase):
    pass