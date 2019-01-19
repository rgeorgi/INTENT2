import re
import unittest
import nltk

from intent2.model import Phrase, SubWord, Word


def is_character_identical(stringA, stringB, skip_re='[#,\-=\.\s]'):
    """
    Returns true if stringA and stringB are represented by identical characters,
    excluding skip chars
    """
    return re.sub(skip_re, '', stringA).lower() == re.sub(skip_re, '', stringB).lower()


class CharacterIdenticalTests(unittest.TestCase):
    def test_positive(self):
        lang_line = "ni,#         ía ba   heyeting-ayoku         ni           yaa,# pun   namei."
        morph_line = "ni           ía ba   he-       yeting-ayoku ni           yaa   pun   namei"

        self.assertTrue(is_character_identical(lang_line, morph_line))

def clean_subword_string(subword_string):
    """
    Remove the characters that a subword is split on.

    :param subword_string:
    """
    return re.sub('[\-=]', '', subword_string)

def word_tokenize(phrase_string):
    """
    Modularizing the tokenization for phrases.

    :param phrase_string:
    :return:
    """
    # split_phrase = re.findall('[\w\.\-\:]+', phrase_string)
    split_phrase = nltk.word_tokenize(phrase_string)
    return split_phrase

def morph_tokenize(word_string):
    """
    Given a word, return the sets of subwords that compose it.
    """
    return [morph for morph in re.split('[\s\-=]+', word_string) if morph.strip()]

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