import unittest
from typing import Generator, Iterable, Iterator, Union




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
        return getattr(self, '_alignment', set([]))

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

class DependencyMixin(object):
    """
    A mixin for items that can have POS dependencies.

    Dependents are children (items with incoming edges to this item)
    Dependency is the item this item has an outgoing edge to
    """
    @property
    def _dependency_links(self):
        """
        :rtype: set[DependencyLink]
        """
        return getattr(self, '_dependencies', set([]))

    @_dependency_links.setter
    def _dependency_links(self, val): setattr(self, '_dependencies', val)

    @property
    def dependencies(self):
        """
        :rtype: set[DependencyLink]
        """
        return {d for d in self._dependency_links if d.child == self}

    @property
    def dependents(self):
        """
        :rtype: set[DependencyLink]
        """
        return {d for d in self._dependency_links if d.parent == self}

    @property
    def dependency_links(self): return self._dependency_links


    def add_dependent(self, dependent, type: str=None):
        add_dependency_link(dependent, self, type=type)

    def add_head(self, head, type: str=None):
        add_dependency_link(self, head, type=type)

def add_dependency_link(child, parent, type=None):
    assert isinstance(child, DependencyMixin)
    assert isinstance(parent, DependencyMixin)
    link = DependencyLink(child, parent, type=type)
    child._dependency_links |= {link}
    parent._dependency_links |= {link}

class StringMixin(object):
    """
    A mixin for words and subwords
    """
    @property
    def string(self): return getattr(self, '_string')

    def __str__(self): return self.string

class MutableStringMixin(StringMixin):
    @property
    def string(self): return getattr(self, '_string')

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
    def __init__(self,
                 child: DependencyMixin,
                 parent: DependencyMixin,
                 type: str=None):
        self.child = child
        self.parent = parent
        self.type = type

    def __repr__(self):
        return '<dep {} --> {}>'.format(self.child, self.parent)

# -------------------------------------------
# Non-Mixin Classes
# -------------------------------------------
class Word(TaggableMixin, AlignableMixin, DependencyMixin, VectorMixin, SpacyTokenMixin, IdMixin):
    """
    Word class

    For word-level items. Every word must contain at least one subword.
    """
    def __init__(self, string=None, subwords=None, id=None):
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
        self._id = id

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
    def hyphenated(self): return '-'.join([str(s) for s in self._subwords])

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

class TransWord(Word): pass
class LangWord(Word): pass
class GlossWord(Word): pass

class SubWord(TaggableMixin, AlignableMixin, MutableStringMixin, LemmatizableMixin, IdMixin):
    """
    Class to represent sub-word level items -- either morphemes or glosses.
    """
    def __init__(self, s, word: Word=None, index=None, id=None):
        self.string = s
        self._index = index
        self._id = id
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
        return ((self.index, part) for part in self.string.split('.'))

    def __repr__(self): return '<sw: {}>'.format(self.string)


class Phrase(list, IdMixin):
    """
    A Phrase object contains a list of words.
    """
    def __init__(self, iterable=None, id=None):
        if iterable is None: iterable = []
        super().__init__(iterable)
        self._root = None
        for i, w in enumerate(self):
            w._phrase = self
            w._index = i
        self.id = id

    @property
    def root(self):
        """:rtype: Word"""
        return self._root

    @root.setter
    def root(self, val): self._root = val

    def add_word(self, w: Word):
        w._index = len(self)
        w._phrase = self
        self.append(w)

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
    def dependencies(self):
        """
        Check all of the dependency relationships of the
        words and return a dependency parse.

        :rtype: set[DependencyLink]
        """
        all_links = set([])
        for word in self:
            all_links |= word._dependency_links
        return all_links

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

class Corpus(object):
    """
    Class for holding a collection
    of instances
    """
    def __init__(self, instances=None):
        self._instances = instances if instances else None

    def __iter__(self):
        """
        :rtype: Iterator[Instance]
        """
        return self._instances.__iter__()

    @property
    def instances(self):
        """:rtype: list[Instance]"""
        return self._instances

    def __getitem__(self, item):
        """:rtype: Instance"""
        return self._instances[item]


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
        self.assertTrue(len(self.wordA.dependencies) == 1)
        dep = next(iter(self.wordA.dependencies))

        # Make sure
        self.assertTrue(dep.child == self.wordB)
        self.assertFalse(dep.child == self.wordA)
        self.assertTrue(dep.parent == self.wordA)
        self.assertFalse(dep.parent == self.wordB)

        # Add one more
        self.wordA.add_dependent(self.wordC)
        self.assertTrue(len(self.wordA.dependencies) == 2)

        depA = self.wordA.dependencies
        depC = self.wordC.dependencies

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
        self.swordA = SubWord('bett')
        self.swordB = SubWord('er')
        self.wordE = Word(subwords=[self.swordA, self.swordB])

    def test_subwords(self):
        self.assertEqual(str(self.wordE), 'better')
        self.assertEqual(self.wordE.hyphenated, 'bett-er')
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
        self.assertEqual(self.wordA)