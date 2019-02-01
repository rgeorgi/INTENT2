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

    def __init__(self, node, children=None, parent_dep_rel=None):
        """
        :param node: The word
        :param children: children trees
        :type children: List[Union[DependencyTree,None]]
        :param parent_dep_rel: Label for dependency relation with parent
        """
        children = [] if children is None else children
        self.parent_dep_rel = parent_dep_rel # The relation of this node to its parent
        super().__init__(node, children=children)

    def pretty_print(self):
        """
        NLTK's pretty_print() wants to do a bunch of
        processing that assumes the node labels are strings.
        :return:
        """
        strcopy = self.copy(tostr=True)
        pt = ParentedTree.convert(strcopy)
        return pt.pretty_print()

    def label(self) -> Word: return super().label()

    def delete(self, promote=True):
        """
        Delete this node, and promote its children
        to take its place.
        """
        if not self.parent():
            raise Exception('Deletion of root unsupported.')
        my_index = self.parent().index(self)

        # Now, insert all of the children into
        # the parent just after the current node.
        if promote:
            for child_i, child in enumerate(self):
                child._parent = None
                self.parent().insert(my_index + child_i + 1, child)

        # Finally, delete the current node from the parent.
        del self.parent()[my_index]

    def __iter__(self):
        """:rtype: Iterator[DependencyTree]"""
        return super().__iter__()

    def copy(self, tostr=False):
        """
        Perform a deep copy of the tree, optionally
        replacing the nodes with string representations,
        since NLTK freaks out if they are not strings.

        :param tostr:
        :rtype: DependencyTree
        """
        new_children = []
        for old_child in self:
            if isinstance(old_child, DependencyTree):
                new_child = old_child.copy(tostr=tostr)
            else:
                new_child = old_child
            new_children.append(new_child)

        if isinstance(self.label(), Word) and tostr:
            label = self.label().hyphenated
        else:
            label = self.label()

        return DependencyTree(label,
                              children=new_children,
                              parent_dep_rel=self.parent_dep_rel)

def build_dt(word: Word, link_type: str = None):
    """
    Recursively build a dt given a node
    and its children.
    """
    children = [build_dt(link.child, link.type)
                for link in sorted(word.dependents,
                                   key=lambda link: link.child.index)]
    return DependencyTree(word, children, link_type)

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