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
    def alignment(self): return getattr(self, '_alignment', default=None)

    @alignment.setter
    def alignment(self, val): setattr(self, '_alignment', val)

class TaggableMixin(object):
    """
    A mixin for items that can have POS tags
    associated with them.
    """
    @property
    def pos(self): return getattr(self, '_pos', default=None)

    @pos.setter
    def pos(self, val): setattr(self, '_pos')

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
        return '<w: {}[{}]>'.format(self.string, self.index)

    def __str__(self):
        return self.string

    @property
    def index(self): return self.phrase.index(self)

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


class Phrase(list):
    def __init__(self, iterable=None):
        if iterable is None: iterable = []
        super().__init__(iterable)
        for w in self:
            w._phrase = self

    def add_word(self, w: Word):
        w.phrase(self)

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
