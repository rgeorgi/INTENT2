import re
import unittest
from collections import defaultdict
from typing import Generator, Iterable, Iterator, Union

class DependencyException(Exception): pass



# -------------------------------------------
# MIXINS
# -------------------------------------------
class AlignableMixin(object):
    """
    A mixin for items that can be aligned with
    another thing.
    """
    @property
    def alignments(self):
        """
        :rtype: set[Union[Word,SubWord]]
        """
        alns = getattr(self, '_alignment', set([]))
        # Also include alignments of subwords if this is a word
        if isinstance(self, Word):
            for sw in self.subwords:
                alns |= sw.alignments
        return alns

    @alignments.setter
    def alignments(self, val): setattr(self, '_alignment', val)

    def add_alignment(self, other):
        assert isinstance(other, AlignableMixin)
        self.alignments |= {other}
        other.alignments |= {self}

    def remove_alignment(self, other):
        assert isinstance(other, AlignableMixin)
        self.alignments -= {other}
        other.alignments -= {self}

class IdMixin(object):
    @property
    def id(self): return getattr(self, '_id', None)

    @id.setter
    def id(self, val): setattr(self, '_id', val)

class IndexableMixin(object):
    @property
    def index(self): return getattr(self, '_index', None)

    @index.setter
    def index(self, val): setattr(self, '_index', val)

class TaggableMixin(object):
    """
    A mixin for items that can have POS tags
    associated with them.
    """
    @property
    def pos(self): return getattr(self, '_pos', None)

    @pos.setter
    def pos(self, val): setattr(self, '_pos', val)

class GlossableMixin(object):
    """
    A mixin for items that can have glosses associated with
    them
    """
    @property
    def gloss(self): return getattr(self, '_gloss', None)

    @gloss.setter
    def gloss(self, val): setattr(self, '_gloss', val)

class DependencyStructure(set):
    """
    A class to implement
    """
    def __init__(self, links = None):
        """
        :type links: Iterable[DependencyLink]
        """
        links = [] if links is None else links
        self._head_map = defaultdict(set)
        self._child_map = defaultdict(set)
        self._roots = set([]) # type: set[Word]
        self._words = set([]) # type: set[Word]
        for link in links:
            self.add(link)

    def __iter__(self):
        """:rtype: DependencyLink"""
        return super().__iter__()

    def copy(self):
        """
        :rtype: DependencyStructure
        """
        new_ds = DependencyStructure()
        for old_link in self: # type: DependencyLink
            new_ds.add(DependencyLink(child=old_link.child,
                                      parent=old_link.parent,
                                      link_type=old_link.type))
        return new_ds

    def add(self, link):
        """
        :type link: DependencyLink
        """
        super().add(link)
        self._add_extra(link)

    def remove(self, link):
        super().remove(link)
        self._remove_extra(link)

    @property
    def roots(self):
        """:rtype: set[Word]"""
        return self._roots

    def depth(self, link, seen_links = None):
        """
        Return the number of links between this link and a root.

        :type link: DependencyLink
        :rtype: int
        """
        if seen_links is None:
            seen_links = set([])
        if link.parent is None:
            return 0
        else:
            parent_links = self.get_parent_links(link.parent)
            filtered_links = {parent_link for parent_link in parent_links if parent_link not in seen_links}
            if not filtered_links:
                raise DependencyException('Cycle found for link "{}"'.format(link))
            else:
                return min({self.depth(parent_link, seen_links=seen_links | parent_links)
                            for parent_link in filtered_links}) + 1


    def remove_word(self, word, promote=True):
        """
        Remove a word from the set of dependency links that

        :param word:
        :param promote:
        :return:
        """
        my_child_links = self.get_child_links(word)
        my_parent_links = self.get_parent_links(word)
        my_parents = {link.parent for link in my_parent_links}

        for child_link in list(my_child_links):
            self.remove(child_link)

            # Add all the children in links that this word
            # parents as links to the parents of this link.
            if promote:
                for parent in my_parents:
                    self.add(DependencyLink(child_link.child, parent, link_type=child_link.type))

        for parent_link in list(my_parent_links):
            self.remove(parent_link)

    def replace_word(self, src_word, tgt_word, remove=True):
        """
        Replace all instances of the source word with the target word.

        If remove is False, the new word will be added as a sibling, rather than in-place.

        :type src_word: Word
        :type tgt_word: Word
        """
        for child_link in list(self.get_child_links(src_word)):
            new_link = DependencyLink(child=child_link.child, parent=tgt_word, link_type=child_link.type)
            if remove:
                self.remove(child_link)
            self.add(new_link)

        for parent_link in list(self.get_parent_links(src_word)):
            new_link = DependencyLink(child=tgt_word, parent=parent_link.parent, link_type=parent_link.type)
            if remove:
                self.remove(parent_link)
            self.add(new_link)


    def _add_extra(self, link):
        self._child_map[link.child].add(link)
        self._head_map[link.parent].add(link)
        if link.parent is None:
            self._roots.add(link.child)
        else:
            self._words.add(link.parent)
        self._words.add(link.child)

    def _remove_extra(self, link):
        self._child_map[link.child].remove(link)
        self._head_map[link.parent].remove(link)
        if link.parent is None:
            self._roots.remove(link.child)

        if not (self._child_map[link.child] or self._head_map[link.child]):
            self._words -= set([link.child])
        if not (self._child_map[link.parent] or self._head_map[link.parent]):
            self._words -= set([link.child])

    @property
    def words(self):
        return sorted(self._words, key=lambda word: word.index)

    def __or__(self, other):
        for link in other:
            self.add(link)

    def __sub__(self, other):
        for link in other:
            self.remove(link)

    def get_parent_links(self, child):
        """
        Return the links in which the given word is the child

        :rtype: set[DependencyLink]
        """
        return self._child_map[child]

    def get_child_links(self, word):
        """
        Return the links in which the given word is the parent
        :rtype: set[DependencyLink]
        """
        return self._head_map[word]

    def visualize(self):
        """
        Visualize the dependency structure.
        """
        def root_or_parent(word):
            if word.parent is None:
                return '_ROOT_'
            else:
                return word.parent.string

        def visualize_word(word):
            parents = ','.join([root_or_parent(w) for w in self.get_parent_links(word)])
            if not parents:
                parents = 'None'
            return '{}->({})'.format(word.string, parents)

        return '[{}]'.format(', '.join(visualize_word(word) for word in self.words))


    def draw(self, name=''):
        from graphviz import Digraph

        dot = Digraph(engine='neato')
        dot.node('_root_', label='ROOT', shape='box', pos='0,3')
        for word in self.words:
            dot.node(word.id, label='{} ({})'.format(word.string, word.id),
                     pos='{},0!'.format(word.index))

        for link in self: # type: DependencyLink
            if link.parent is None:
                dot.edge(link.child.id, '_root_', label='ROOT')
            else:
                dot.edge(link.child.id, link.parent.id,
                         label=link.type, constraint='false', fillcolor='blue')


        dot.attr(overlap='false', splines='curved', sep='5', esep='3')

        # dot.attr(esep='20')
        # dot.attr(splines='true')

        dot.render('/tmp/{}'.format(name))



class DependencyMixin(object):
    """
    A mixin for items that can have dependency structures.

    (This is defined to just be a phrase)
    """

    @property
    def dependency_structure(self):
        """:rtype: DependencyStructure"""
        return getattr(self, '_ds', None)

    @dependency_structure.setter
    def dependency_structure(self, val):
        setattr(self, '_ds', val)


class StringMixin(object):
    """
    A mixin for words and subwords
    """
    @property
    def string(self): return getattr(self, '_string')

    def __str__(self): return self.string

class MutableStringMixin(StringMixin):
    @property
    def string(self) -> str: return getattr(self, '_string')

    @string.setter
    def string(self, val): setattr(self, '_string', val)


class LemmatizableMixin(object):
    """
    A mixin for objects that could be lemmatizable
    """
    @property
    def lemma(self): return getattr(self, '_lemma')

    @lemma.setter
    def lemma(self, val): setattr(self, '_lemma', val)

class VectorMixin(object):
    """
    A mixin to add a vector representation to objects
    """
    @property
    def vector(self): return getattr(self, '_vector')

    @vector.setter
    def vector(self, val): setattr(self, '_vector', val)

class SpacyTokenMixin(object):
    """
    A mixin to add a vector representation to objects
    """
    @property
    def spacy_token(self): return getattr(self, '_spacy_token')

    @spacy_token.setter
    def spacy_token(self, val): setattr(self, '_spacy_token', val)

# -------------------------------------------
# Structures
# -------------------------------------------
class DependencyLink(object):
    def __init__(self, child=None, parent=None,
                 link_type: str=None):
        """
        :type child: Word
        :type parent: Word
        """
        self.child = child
        self.parent = parent
        self.type = link_type

    def __repr__(self):
        ret_str = '<dep {} --> {}'.format(self.child, self.parent)
        if self.type:
            ret_str += ' ({})'.format(self.type)
        return ret_str + '>'


    def __hash__(self):
        return hash((self.child, self.parent, self.type))

    def __eq__(self, other):
        return (self.child == other.child
                and self.parent == other.parent
                and self.type == other.type)




# -------------------------------------------
# Non-Mixin Classes
# -------------------------------------------
class Word(TaggableMixin, AlignableMixin, DependencyMixin, VectorMixin, SpacyTokenMixin, IdMixin):
    """
    Word class

    For word-level items. Every word must contain at least one subword.
    """
    def __init__(self, string=None, subwords=None, id_=None):
        """

        :param string:
        :param subwords:
        :type subwords: Iterable[SubWord]
        :param id_:
        """
        assert (string or subwords) and not (string and subwords)
        if string is not None:
            self._subwords = [SubWord(string, word=self, index=0)]
        else:
            self._subwords = subwords
            for i, sw in enumerate(self._subwords):
                if isinstance(sw, str):
                    self._subwords[i] = SubWord(sw)
                self._subwords[i].word = self
                self._subwords[i]._index = i
        self._phrase = None
        self._index = None
        self._id = id_

    def __repr__(self):
        return '(w: {} [{}])'.format(', '.join([repr(sw) for sw in self.subwords]), self.index)

    def __str__(self):
        return self.hyphenated

    def __iter__(self):
        """
        :rtype: Iterator[SubWord]
        """
        return self._subwords.__iter__()

    def __getitem__(self, item):
        """
        :rtype: SubWord
        """
        return self.subwords[item]

    def equals(self, other):
        """
        Equals method that doesn't muck with the == method.
        """
        return (self.hyphenated == other.hyphenated and self.index == other.index and
                ((self.id is None or other.id is None) or (self.id == other.id)))

    @property
    def index(self): return self._index

    @property
    def hyphenated(self):
        return ''.join([s.hyphenated for s in self._subwords])

    @property
    def string(self): return ''.join([str(s) for s in self._subwords])

    @property
    def phrase(self): return self._phrase

    @property
    def subwords(self):
        """:rtype: Iterable[SubWord]"""
        return self._subwords

    @property
    def subword_parts(self):
        """:rtype: Generator[tuple[float, str]]"""
        for sw in self.subwords:
            for part in sw.parts:
                yield part

    @property
    def lemma(self):
        assert len(self.subwords) == 1
        return self[0].lemma

    @property
    def word(self): return self

class TransWord(Word):

    @property
    def aligned_lang_words(self):
        """
        The normal behavior for TransWords is to be aligned to gloss
        words or morphemes. This function returns the set of language
        words that those gloss words/morphemes are aligned to (or
        LangWords, if they're aligned directly).

        :rtype: set[LangWord]
        """
        ret_words = set([])
        for aligned_item in self.alignments:

            # Get the aligned word for this item,
            # which should be a gloss or
            if isinstance(aligned_item, SubWord):
                aligned_word = aligned_item.word
            elif isinstance(aligned_item, Word):
                aligned_word = aligned_item

            if isinstance(aligned_word, LangWord):
                ret_words.add(aligned_item)
            else:
                ret_words |= {w for w in aligned_word.alignments if isinstance(w, LangWord)}
        return ret_words


class LangWord(Word): pass
class GlossWord(Word): pass

class SubWord(TaggableMixin, AlignableMixin, MutableStringMixin, LemmatizableMixin, IdMixin):
    """
    Class to represent sub-word level items -- either morphemes or glosses.
    """
    def __init__(self, s, word: Word=None, index=None, id_=None,
                 left_symbol: str = None, right_symbol: str = None):
        """

        :param s: The string value of the word
        :param word: The parent object that contains this subword
        :param index: The index of this object within its parent
        :param id_: A string representing this object uniquely
        :param left_symbol: A string that combines this symbol with the token to the left (e.g. - or =)
        :param right_symbol: A string that combines this symbol with the token to the right
        """
        self.string = s
        self._index = index
        self._id = id_
        self.left_symbol = left_symbol
        self.right_symbol = right_symbol
        if word is not None:
            self.word = word

    @property
    def word(self): return self._word

    @word.setter
    def word(self, w): self._word = w

    @property
    def index(self):
        return float('{}.{}'.format(self.word.index, self._index))

    @property
    def parts(self):
        """
        Return the period-or-slash-delineated portions of a sub-word.
        """
        return ((self.index, part) for part in re.split('[\./]', self.string) if part)

    @property
    def hyphenated(self):
        """
        :return: A string joining the subwords with the appropriate -, =, etc. to indicate
                 morpheme segmentation.
        :rtype: str
        """
        ret_str = ''
        if self.left_symbol:
            ret_str += self.left_symbol
        ret_str += self.string
        if self.right_symbol:
            ret_str += self.right_symbol
        return ret_str

    def __repr__(self): return '<sw: {}>'.format(self.hyphenated)

    def __eq__(self, other):
        return (self.string == other.string
                and self.left_symbol == other.left_symbol
                and self.right_symbol == other.right_symbol
                and self.id == other.id)

    def __hash__(self):
        return hash(self.hyphenated + '-' + self.id)


class Phrase(list, IdMixin, DependencyMixin):
    """
    A Phrase object contains a list of words.
    """
    def __init__(self, iterable=None, id_=None):
        if iterable is None: iterable = []
        super().__init__(iterable)
        for i, w in enumerate(self):
            w._phrase = self
            w._index = i
        self.id = id_


    def add_word(self, w: Word):
        w._index = len(self)
        w._phrase = self
        self.append(w)

    def append(self, w: Word):
        w._index = len(self)
        super().append(w)

    def __getitem__(self, i):
        """
        :rtype: Word
        """
        if isinstance(i, int):
            return super().__getitem__(i)
        if isinstance(i, float):
            w_index, sw_index = (int(part) for part in str(i).split('.'))
            return super().__getitem__(w_index)[sw_index]

    def __iter__(self):
        """
        :rtype: Iterator[Word]
        """
        return super().__iter__()

    def equals(self, other):
        return bool(len(self) == len(other) and [True for i, j in zip(self, other) if i.equals(j)])

    @classmethod
    def from_string(cls, s):
        return cls([Word(w) for w in s.split()])

    @property
    def hyphenated(self): return ' '.join([w.hyphenated for w in self])

    def __str__(self):
        return ' '.join([str(s) for s in self]) if self else ''

    def __repr__(self):
        return '[p: {}]'.format(', '.join([repr(s) for s in self]))

    @property
    def subwords(self):
        """
        Return all the subwords
        :rtype: Generator[SubWord]
        """
        for word in self:
            for subword in word:
                yield subword

    @property
    def alignments(self):
        """
        Return all the alignments
        :rtype: Iterable[AlignableMixin]
        """
        alignments = []
        for elt in self:
            for aligned_elt in elt.alignments:
                alignments.append((elt, aligned_elt))
        return alignments


class Instance(IdMixin):
    """
    This class represents an entire IGT instance. It supposes
    that
    """
    def __init__(self, lang=None, gloss=None, trans=None, id=None):
        """
        :type lang: Phrase
        :type gloss: Phrase
        :type trans: Phrase
        """
        self.lang = lang
        self.gloss = gloss
        self.trans = trans
        self._id = id

    def __str__(self):
        max_token_len = [0 for i in range(max(len(self.lang), len(self.gloss)))]

        def compare_len(phrase):
            for i, word in enumerate(phrase):
                max_token_len[i] = max(max_token_len[i], len(str(word)))

        compare_len(self.lang)
        compare_len(self.gloss)

        ret_str = ''
        for phrase in [self.lang, self.gloss]:
            for i, word in enumerate(phrase):
                ret_str += '{{:<{}}}'.format(max_token_len[i]+2).format(str(word))
            ret_str = ret_str + '\n' if phrase else ret_str

        return ret_str + str(self.trans)

    def __repr__(self):
        return '<IGT Instance with {} words>'.format(len(self.lang))

class Corpus(list):
    """
    Class for holding a collection
    of instances
    """
    def __init__(self, instances=None):
        super().__init__(instances)

    def __iter__(self):
        """
        :rtype: Iterator[Instance]
        """
        return super().__iter__()


# -------------------------------------------
# Tests
# -------------------------------------------

def setUpPhrase(o):
    o.wordA = Word('ran')
    o.wordB = Word('John')
    o.wordC = Word('around')
    o.phrase = Phrase([o.wordB, o.wordA, o.wordC])

class DependencyTests(unittest.TestCase):
    def setUp(self):
        setUpPhrase(self)

    def test_dependencies(self):
        self.wordA.add_dependent(self.wordB)
        self.assertTrue(len(self.wordA.dependency_links) == 1)
        dep = next(iter(self.wordA.dependency_links))

        # Make sure
        self.assertTrue(dep.child == self.wordB)
        self.assertFalse(dep.child == self.wordA)
        self.assertTrue(dep.parent == self.wordA)
        self.assertFalse(dep.parent == self.wordB)

        # Add one more
        self.wordA.add_dependent(self.wordC)
        self.assertTrue(len(self.wordA.dependency_links) == 2)

        depA = self.wordA.dependency_links
        depC = self.wordC.dependency_links

        self.assertTrue(len(depA & depC) == 1)

class PhraseTests(unittest.TestCase):
    def setUp(self):
        setUpPhrase(self)

    def test_phrase(self):
        self.assertEqual(len(self.phrase), 3)
        self.assertEqual(self.phrase[0].hyphenated, 'John')
        self.assertEqual(self.phrase[1].hyphenated, 'ran')
        self.assertEqual(self.phrase[2].hyphenated, 'around')

        self.assertEqual(self.wordA.index, 1)
        self.assertEqual(self.wordB.index, 0)
        self.assertEqual(self.wordC.index, 2)

    def test_string_creator(self):
        p = Phrase.from_string('Person Spc money take.Pfv father 3.loc-give.Ipfv')
        p2 = Phrase([Word('Person'), Word('Spc'), Word('money'), Word('take.Pfv'),
                     Word('father'), Word('3.loc-give.Ipfv')])

        for w1, w2 in zip(p, p2):
            self.assertTrue(w1.equals(w2))
        self.assertTrue(p.equals(p2))
        self.assertNotEqual(p, p2)
        self.assertEqual(p[0].hyphenated, Word('Person').hyphenated)
        self.assertEqual(p[1].hyphenated, Word('Spc').hyphenated)
        self.assertEqual(p[2].hyphenated, Word('money').hyphenated)


class WordTests(unittest.TestCase):
    def setUp(self):
        self.wordD = Word('Test')
        self.swordA = SubWord('bett', right_symbol='-')
        self.swordB = SubWord('er')
        self.swordC = SubWord('bett', right_symbol='=')
        self.wordE = Word(subwords=[self.swordA, self.swordB])
        self.wordF = Word(subwords=[self.swordC, self.swordB])

    def test_subword_strings(self):
        self.assertEqual(self.wordE.string, 'better')
        self.assertEqual(self.wordE.hyphenated, 'bett-er')
        self.assertEqual(self.wordF.string, 'better')
        self.assertEqual(self.wordF.hyphenated, 'bett=er')
        self.assertEqual(len(self.wordE.subwords), 2)

    def test_word_equivalencies(self):
        p = Phrase.from_string('That John is a different John from the one I know.')
        w1 = p[1]
        w5 = p[5]
        self.assertEqual(w1.hyphenated, w5.hyphenated)
        self.assertNotEqual(w1, w5)


class AlignmentTests(unittest.TestCase):
    def setUp(self):
        self.l = Phrase.from_string('Ama nu seng mii maama hel')
        self.g = Phrase.from_string('person Spc money take.Pfv father 3.loc-give.Ipfv')
        for lw, gw in zip(self.l, self.g):
            lw.add_alignment(gw)

        self.w1 = Word('test')
        self.w2 = Word('exam')
        self.w3 = Word('quiz')

    def test_phrasal_alignments(self):
        pass

    def test_add_alignment(self):
        self.assertFalse(self.w1.alignments)
        self.assertFalse(self.w2.alignments)

        self.w1.add_alignment(self.w2)
        self.assertTrue(self.w1.alignments)
        self.assertTrue(self.w2.alignments)

        self.assertEqual(next(iter(self.w1.alignments)), self.w2)
        self.assertEqual(next(iter(self.w2.alignments)), self.w1)

    def test_remove_alignment(self):
        self.w1.add_alignment(self.w2)
        self.w1.add_alignment(self.w3)

        self.assertEqual(len(self.w1.alignments), 2)

        self.w1.remove_alignment(self.w2)
        self.assertEqual(len(self.w1.alignments), 1)

        self.assertEqual(next(iter(self.w1.alignments)), self.w3)
        self.assertEqual(len(self.w2.alignments), 0)

class TagTests(unittest.TestCase):
    def setUp(self):
        setUpPhrase(self)

    def test_pos_tag(self):
        self.assertIsInstance(self.wordA, Word)
        self.assertIsNone(self.wordA.pos)
        self.wordA.pos = 'NN'
        self.assertIsNotNone(self.wordA.pos)
