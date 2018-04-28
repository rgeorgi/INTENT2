import unittest


# -------------------------------------------
# MIXINS
# -------------------------------------------
class AlignableMixin(object):
    """
    A mixin for items that can be aligned with
    another thing.
    """
    @property
    def alignments(self): return getattr(self, '_alignment', set([]))

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

class TaggableMixin(object):
    """
    A mixin for items that can have POS tags
    associated with them.
    """
    @property
    def pos(self): return getattr(self, '_pos', None)

    @pos.setter
    def pos(self, val): setattr(self, '_pos', val)

class DependencyMixin(object):
    """
    A mixin for items that can have POS dependencies.

    Dependents are children (items with incoming edges to this item)
    Dependency is the item this item has an outgoing edge to
    """
    @property
    def dependencies(self):
        """
        :rtype: list[DependencyLink]
        """
        return getattr(self, '_dependencies', set([]))

    @dependencies.setter
    def dependencies(self, val): setattr(self, '_dependencies', val)

    def add_dependent(self, dependent, type: str=None):
        assert isinstance(dependent, DependencyMixin)
        link = DependencyLink(dependent, self, type = type)
        self.dependencies |= {link}
        dependent.dependencies |= {link}

class StringMixin(object):
    """
    A mixin for words and subwords
    """
    @property
    def string(self): return getattr(self, '_string')

    @string.setter
    def string(self, val): setattr(self, '_string', val)

    def __str__(self): return self.string


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
class Word(TaggableMixin, AlignableMixin, DependencyMixin):
    """
    Word class

    For word-level items. Every word must contain at least one subword.
    """
    def __init__(self, string=None, subwords=None):
        assert (string or subwords) and not (string and subwords)
        if string is not None:
            self._subwords = [SubWord(string, word=self)]
        else:
            self._subwords = subwords
        self._phrase = None

    def __repr__(self):
        return '(w: {} [{}])'.format(', '.join([repr(sw) for sw in self.subwords]), self.index)

    def __str__(self):
        return self.string

    def equals(self, other):
        """
        Equals method that doesn't muck with the == method.
        """
        return self.string == other.string and self.index == other.index

    @property
    def index(self): return self.phrase.index(self) if self.phrase else None

    @property
    def string(self): return ''.join([str(s) for s in self._subwords])

    @property
    def hyphenated(self): return '-'.join([str(s) for s in self._subwords])

    @property
    def phrase(self): return self._phrase

    @property
    def subwords(self): return self._subwords

class SubWord(TaggableMixin, AlignableMixin, DependencyMixin, StringMixin):
    def __init__(self, s, word=None):
        self.string = s
        if word is not None:
            self.word = word

    @property
    def word(self): return self._word

    @word.setter
    def word(self, w): self._word = w

    def __repr__(self): return '<sw: {}>'.format(self.string)


class Phrase(list):
    def __init__(self, iterable=None):
        if iterable is None: iterable = []
        super().__init__(iterable)
        for w in self:
            w._phrase = self

    def add_word(self, w: Word):
        self.append(w)
        w._phrase = self

    def __getitem__(self, i) -> Word:
        return super().__getitem__(i)

    def equals(self, other):
        return bool(len(self) == len(other) and [True for i, j in zip(self, other) if i.equals(j)])

    @classmethod
    def from_string(cls, s):
        return cls([Word(w) for w in s.split()])

    @property
    def hyphenated(self): return ' '.join([w.hyphenated for w in self])

    def __str__(self): return ' '.join([str(s) for s in self])

    def __repr__(self): return '[p: {}]'.format(', '.join([repr(s) for s in self]))

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
        self.assertEqual(self.phrase[0].string, 'John')
        self.assertEqual(self.phrase[1].string, 'ran')
        self.assertEqual(self.phrase[2].string, 'around')

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
        self.assertEqual(p[0].string, Word('Person').string)
        self.assertEqual(p[1].string, Word('Spc').string)
        self.assertEqual(p[2].string, Word('money').string)


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
        self.assertEqual(w1.string, w5.string)
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