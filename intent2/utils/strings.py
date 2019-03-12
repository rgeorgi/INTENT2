import re
import unittest
import nltk

from intent2.model import Phrase, SubWord, Word

import logging
STRING_LOG = logging.getLogger('string')

# -------------------------------------------
# Some String Constants
# -------------------------------------------

# Any character in this list will be considered
# one that splits morphemes
MORPH_SYMBOLS = ['-', '=', ':']
MORPH_RE = '[{0}]'.format(''.join(['\\' + sym for sym in MORPH_SYMBOLS]))
MORPH_SEG_RE = '{}|$'.format(MORPH_RE)


class StringException(Exception): pass
class StringSegmentationException(StringException): pass

# -------------------------------------------

def word_str_to_subwords(w: str):
    """
    Given a word string, create a subword components.
    :param w:
    :return:
    """

    # Remove whitespace
    w = re.sub('\s', '', w)

    # Iteratively look for the next morpheme break or
    # end of string, and the
    subwords = []
    last_index = 0
    for morph_position in re.finditer(MORPH_SEG_RE, w):
        start, stop = morph_position.span()
        morph_str = w[last_index:start]
        morph_sep = w[start:stop]
        sw = SubWord(morph_str, right_symbol=morph_sep if morph_sep else None)
        subwords.append(sw)
        last_index = stop
    return subwords



def is_character_identical(stringA, stringB, skip_re='[#,\-=\.\s]'):
    """
    Returns true if stringA and stringB are represented by identical characters,
    excluding skip chars
    """
    return re.sub(skip_re, '', stringA).lower() == re.sub(skip_re, '', stringB).lower()

# -------------------------------------------
# Test Cases
# -------------------------------------------

class CharacterIdenticalTests(unittest.TestCase):
    def test_positive(self):
        lang_line = "ni,#         ía ba   heyeting-ayoku         ni           yaa,# pun   namei."
        morph_line = "ni           ía ba   he-       yeting-ayoku ni           yaa   pun   namei"

        self.assertTrue(is_character_identical(lang_line, morph_line))

class SubWordCreationTests(unittest.TestCase):
    def test_clitics(self):
        w_str = 'this=clitic'
        subwords = [SubWord('this', right_symbol='='),
                    SubWord('clitic')]
        self.assertListEqual(word_str_to_subwords(w_str),
                             subwords)

# -------------------------------------------

def subword_str_to_subword(subword_string, id_=None, word: Word = None):
    """
    Given a string representing a subword, return the
    subword object from it.

    :param subword_string:
    :return: A SubWord object, given
    """
    # Check for left and rightmost characters being
    # morpheme segmentation.
    original_subword = subword_string
    left_seg, right_seg = None, None
    if subword_string[0] in MORPH_SYMBOLS:
        left_seg = subword_string[0]
        subword_string = subword_string[1:]
    if not subword_string:
        STRING_LOG.info('Subword "{}" appears to only contain a morph separator.'.format(original_subword))
    elif subword_string[-1] in MORPH_SYMBOLS:
        right_seg = subword_string[-1]
        subword_string = subword_string[:-1]

    return SubWord(subword_string, left_symbol=left_seg, right_symbol=right_seg, id_=id_, word=Word)

def word_tokenize(phrase_string):
    """
    Modularizing the tokenization for phrases.

    :param phrase_string:
    :return:
    """
    # split_phrase = re.findall('[\w\.\-\:]+', phrase_string)
    split_phrase = nltk.word_tokenize(phrase_string)
    return split_phrase

def character_align(word_string, subword_string, skip_re='[\-\s]'):
    """
    Given a word-level line and a subword-level line that are character aligned,
    (with the exception of the characters to skip), link the subword-level string
    to the words of the word-level string.
    """
    p = Phrase()

    word_strings = word_string.split()
    cur_subwords = []
    word_idx = 0

    # Iterate through all the whitespace-separated subwords.
    subwords = [SubWord(sw) for sw in re.split('[\s\-]+', subword_string)]
    for subword in subwords:


        if not re.search(re.sub(skip_re, '', subword.string), word_strings[word_idx], flags=re.IGNORECASE):
            w = Word(subwords=cur_subwords)
            cur_subwords = []
            p.add_word(w)
            word_idx += 1

        cur_subwords.append(subword)


    print(p.hyphenated)
    print([w.subwords for w in p])