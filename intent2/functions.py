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

ENRICH_LOG = logging.getLogger('enrich')

# -------------------------------------------
# Dependency Parsing
# -------------------------------------------
class DependencySet(set[DependencyLink]):
    """
    Rather than representing a dependency structure
    as a tree, just keep it as a set of links between
    items.
    """
    def __new__(cls, iterable: Iterable=None, root: DependencyLink=None):
        if iterable is None:
            iterable = []
        ds = cls(iterable)


def extract_ds(p: Phrase):
    """
    Given a phrase that's been assigned a dependency analysis,
    extract it as a tree that can be manipulated and traversed.

    A dependency tree needs:
       * Parent
       * Child
       * Edge label
    """
    dep_links = p.dependency_links

    # --1) Look for links with no
    roots = []
    for dep_link in dep_links:
        if dep_link.parent is None:
            roots.append(dep_link.child)

    if len(roots) > 1:
        ENRICH_LOG.error('Multiple roots found for dependency tree in instance phrase "{}"'.format(p.id))
        raise Exception('Handling multiple roots not implemented')
    else:
        # Return with a dummy root, so that
        # in case the actual root is deleted,
        # we can return a tree with multiple roots.
        return DependencyTree('_ROOT_',
                              [build_dt(roots[0], 'root')],
                              '_ROOT_')

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
    # -- 0) Start by extracting the dependency
    #      tree from the translation.
    process_trans_if_needed(inst)
    t_ds = extract_ds(inst.trans)

    # -- 1) Copy English DS and remove unaligned words.
    proj_ds = t_ds.copy()

    proj_ds.pretty_print()

    nodes = list(proj_ds.subtrees())
    for node in nodes:
        if not node._label.alignments:
            node.delete()

    proj_ds.pretty_print()



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

from unittest import TestCase
class DepTreeTests(TestCase):
    def test_delete_root(self):
        dt = DependencyTree('_ROOT_', [], '_ROOT_')
        self.assertRaises(Exception, dt.delete)

    def test_deletion_promotes(self):
        orig_dt = DependencyTree('_ROOT_', [
            DependencyTree('a', [DependencyTree('b')]),
            DependencyTree('c')
        ])
        tgt_dt = DependencyTree('_ROOT_', [
            DependencyTree('b'),
            DependencyTree('c')
        ])

        orig_dt[0].delete(promote=True)
        self.assertEqual(orig_dt, tgt_dt)

    def test_deletion_no_promotes(self):
        orig_dt = DependencyTree('_ROOT_', [
            DependencyTree('a', [DependencyTree('b')]),
            DependencyTree('c')
        ])
        tgt_dt = DependencyTree('_ROOT_', [
            DependencyTree('c')
        ])

        orig_dt[0].delete(promote=False)
        self.assertEqual(orig_dt, tgt_dt)