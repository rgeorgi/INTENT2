"""
This file is to be used for the main
tricky code implementations of INTENT,
namely:

    * Projecting annotation
    * Performing alignment

"""
import collections

from intent2.model import Instance, Word, SubWord, Phrase
import spacy
from typing import Iterable, Generator, List, Tuple
from spacy.language import Language
from spacy.tokens import Doc, Span, Token
import logging

ALIGN_LOG = logging.getLogger('alignment')
ENRICH_LOG = logging.getLogger('enrich')

global SPACY_ENG # type: Language
SPACY_ENG = None


def load_spacy():
    """
    Lazy-load the spacy model when needed.
    :return:
    """
    global SPACY_ENG
    if SPACY_ENG is None:
        SPACY_ENG = spacy.load('en_core_web_lg')  # type: Language
    return SPACY_ENG


def process_trans(inst: Instance, tag=True, parse=True):
    """
    Apply the SpaCy pipeline to the translation sentence.

    :type inst: Instance
    """
    # Parsing requires a translation line
    assert inst.trans

    spacy_eng = load_spacy()
    trans_string = spacy_eng.tokenizer.tokens_from_list([w.string for w in inst.trans])

    # Tag and parse
    spacy_eng.tagger(trans_string)
    spacy_eng.parser(trans_string)

    # Now let's go through the words, and assign attributes to them.
    assert len(inst.trans) == len(trans_string)
    for i in range(len(inst.trans)):
        trans_word = inst.trans[i]
        spacy_word = trans_string[i] # type: Token

        # Add POS Tag
        if tag:
            trans_word.pos = spacy_word.pos_

        # Add Dependency Head
        if parse:
            if spacy_word.head.i != i:
                trans_word.add_head(inst.trans[spacy_word.head.i])
            # If spacy says that a word is its own head,
            # it is the root.
            else:
                inst.trans.root = trans_word

        # Add vector
        trans_word.spacy_token = spacy_word

        # Add lemmatization
        assert len(trans_word.subwords) == 1
        trans_word[0].lemma = spacy_word.lemma_
        # TODO: Should there be a case where a translation word has more than one subword?




# -------------------------------------------
# Heuristic Alignment
# -------------------------------------------


def find_matches(trans_w: Word, gloss_parts: List[Tuple[float, Token]], match_func):
    """
    Given a translation word to match, a target phrase on which to iterate, and
    a matching function, return a list of indices that match.

    :rtype: List[Tuple[float, Token]]
    """
    matches = [gloss_part for gloss_part in gloss_parts if match_func(trans_w, gloss_part)]
    return matches


def exact_match(trans_w: Word, gloss_part: Tuple[float, Token]):
    return trans_w.string.lower() == gloss_part[1].text.lower()

def lemma_match(trans_w: Word, gloss_part: Tuple[float, Token]):
    """
    See if stemming the gloss portion and the translation word
    results in a match
    """
    assert trans_w.lemma is not None
    return trans_w.lemma.lower() == gloss_part[1].lemma_.lower()

def gram_match(trans_w: Word, gloss_part: Tuple[float, Token]):
    """
    See if the rendering of the translation word might instead be
    compactly represented by inflectional information in the gloss
    line. For instance, "we" might not be expressed explicitly in
    the gloss, but instead implicit as "1pl"
    """
    return trans_w.string.lower() in gramdict.get(gloss_part[1].text.lower(), [])

def substring_match(trans_w: Word, gloss_part: Tuple[float, Token]):
    """
    Is either one of the translation words an exact substring of
    one of the glosses, or one of the glosses an exact substring
    of one of the translation words.
    """
    minimum_length = 3
    trans_str = trans_w.string.lower()
    gloss_str = gloss_part[1].text.lower()

    return (len(trans_str) >= minimum_length and trans_str in gloss_str or
            len(gloss_str) >= minimum_length and gloss_str in trans_str)

def vector_match(trans_w: Word, gloss_part: Tuple[float, Token]):
    """
    Use spaCy's word embeddings to calculate similarity between
    a translation word and part of a gloss with the idea that this
    may capture related words like "hill :: mountain"

    Note that this risks picking up related, but not synonymous terms,
    like "second :: fifth" or "money :: stocks"
    """
    raise Exception('Not fully implemented yet')
    print(trans_w.string, gloss_part[1].text)
    print(gloss_part[1].similarity(trans_w.spacy_token))


# -------------------------------------------
heur_map = {'vec':vector_match,
            'exact':exact_match,
            'lemma':lemma_match,
            'gram':gram_match,
            'sub':substring_match}

gramdict = {'1sg': ['i', 'me'],
            '1pl' : ['we', 'us', 'our'],
            'det': ['the', 'this'],
            '3pl': ['they'],
            '3sg': ['he', 'she', 'him', 'her'],
            '3sgf': ['she', 'her'],
            '2sg': ['you'],
            '3sgp': ['he'],
            'poss': ['his', 'her', 'my', 'their'],
            'neg': ["n't", 'not'],
            '2pl': ['you']}

def heuristic_alignment(inst: Instance, heur_list = None):
    """
    Implement the alignment between words

    :type inst: Instance
    """

    print(inst, end='\n\n')

    # To do heuristic alignment, we need minimally a gloss and translation line.
    assert inst.gloss and inst.trans and inst.lang

    # We don't need to store the sub-sub-word information that we will use to perform
    # alignment, but we want to get things like the lemmas and vector representations
    # of the period-separated portions, so let's get those here.
    gloss_parts = []
    for gloss_w in inst.gloss:
        gloss_parts.extend(gloss_w.subword_parts)

    spacy_eng = load_spacy()
    gloss_part_doc = spacy_eng.tokenizer.tokens_from_list([part[1] for part in gloss_parts])
    # spacy_eng.tagger(gloss_part_doc)
    # spacy_eng.parser(gloss_part_doc)

    # Form the "gloss_parts" list consisting of tuples of subword indices and their analyzed components,
    # so that we can make comparisons yet still retrieve the word and subword for alignment purposes.
    gloss_parts = list(zip([p[0] for p in gloss_parts], gloss_part_doc)) # type: List[Tuple[float, Token]]


    # Let's also define a local function to look for matches between translation words
    # and parts of the gloss.
    def alignment_pass(match_func):
        align_strs = []
        alignments = []
        for trans_w in inst.trans:
            for gloss_part_index, token in find_matches(trans_w, gloss_parts, match_func):
                alignments.append((trans_w.index, gloss_part_index))
                align_strs.append('{0}[{1}]--[{3}]{4}'.format(trans_w.string, trans_w.index, token, gloss_part_index, inst.gloss[gloss_part_index].word))

        # Output debug of results of the alignment
        if alignments:
            ALIGN_LOG.debug('heuristic "{}" produced: {}'.format(
                match_func.__name__,
                ', '.join(align_strs)
            ))
        else:
            ALIGN_LOG.debug('heuristic "{}" produced no matches.'.format(match_func.__name__))
        # TODO: Add debug logging for what multiple alignment reduction does.
        return alignments

    # Now, what we'll want to do:
    #    Iteratively match via a heuristic backoff 'filter' starting from the most precise matches
    #    to those with the most recall.
    #
    #       1. Exact match
    #       2. Lemma match
    #       3. Common gram substitutions (1pl="we" for instance)

    # First, let's take a look for exact matches on the language line, in case there are
    # any proper names.
    # TODO: Modularize this better
    existing_alignments = set([])
    for lang_w in inst.lang:
        for trans_w in inst.trans:
            if lang_w.string.lower() == trans_w.string.lower():
                existing_alignments.add((trans_w.index, lang_w.index))
                existing_alignments = handle_multiple_alignments(existing_alignments)

    # The "heur_list" is the list defining which, and the
    # order of which heuristics to use for alignment.
    if heur_list is None:
        heur_list = ['exact', 'lemma', 'sub', 'gram']

    for match_func, heur_str in [(heur_map.get(heur_str), heur_str) for heur_str in heur_list]:
        if match_func is None:
            raise Exception('Invalid match method "{}" passed to heuristic alignment.'.format(heur_str))

        # 1) Obtain the alignments
        new_alignments = alignment_pass(match_func)

        # 2) Remove alignments that would conflict with already defined alignments
        # TODO: How best to merge newly proposed alignments?
        new_alignments = remove_conflicting_alignments(existing_alignments, new_alignments)

        # 3) Handle multiple alignmnets
        new_alignments = handle_multiple_alignments(new_alignments)

        # 4) Merge with existing alignments
        existing_alignments |= set(new_alignments)

    # Now that we have all of the alignments, let's translate those
    # into alignments on the words.
    for word_index, gloss_index in existing_alignments:
        trans_w = inst.trans[word_index]
        gloss_m = inst.gloss[gloss_index]
        trans_w.add_alignment(gloss_m)

    print(inst.trans.alignments)

def get_alignment_words(alignments: List[Tuple[int, float]]):
    return {word_index for word_index, gloss_index in alignments}

def get_alignment_glosses(alignments: List[Tuple[int, float]]):
    return {gloss_index for word_index, gloss_index in alignments}

def remove_conflicting_alignments(existing_alignments: List[Tuple[int, float]],
                                  new_alignments: List[Tuple[int, float]]):
    """
    Remove any newly proposed alignments that overlap with already
    assigned alignments
    """
    aligned_words = get_alignment_words(existing_alignments)
    aligned_glosses = get_alignment_glosses(existing_alignments)
    return [(word_index, gloss_index) for word_index, gloss_index in new_alignments
            if word_index not in aligned_words
            and gloss_index not in aligned_glosses]


def alignments_to_dict(alignments: List[Tuple[int, float]], key_is_gloss=True):
    """:rtype: dict[list]"""
    ret_alignments = {}

    key_index, compare_index = (0, 1) if key_is_gloss else (1, 0)
    retrieval_func = get_alignment_glosses if key_is_gloss else get_alignment_words

    for aligned_index in retrieval_func(alignments):
        ret_alignments[aligned_index] = sorted([a[key_index] for a in alignments if a[compare_index] == aligned_index])
    return ret_alignments

def handle_multiple_alignments(alignments: List[Tuple[int, float]]):
    """
    Check for multiple alignments between potential gloss tokens and translations.

    Candidate tokens are aligned left to right monotonically, with any remaining
    tokens assigned to the last aligned token.

    :rtype: List[Tuple[int, float]]
    """
    final_alignments = set([])

    gloss_mapping = alignments_to_dict(alignments)
    word_mapping = alignments_to_dict(alignments, key_is_gloss=False)

    unaligned_glosses = set(get_alignment_glosses(alignments))
    unaligned_words = set(get_alignment_words(alignments))

    # First, monotonically assign one alignment between glosses and words
    for gloss_to_align in sorted(gloss_mapping.keys()):
        # First, attempt to skip any words that have already been aligned.
        words_to_align = [word_index for word_index in gloss_mapping.get(gloss_to_align)
                          if word_index in unaligned_words]

        # If there are viable candidates, assign the gloss this mapping.
        # if all words this gloss is aligned to are already aligned,
        # go ahead and assign it to the rightmost possible.
        if words_to_align:
            word_to_align = words_to_align[0]
        if not words_to_align:
            word_to_align = gloss_mapping.get(gloss_to_align)[-1]

        final_alignments.add((word_to_align, gloss_to_align))
        unaligned_glosses.remove(gloss_to_align)
        unaligned_words -= {word_to_align}

    # Next, assign any unaligned words to the first gloss that is available.
    for word_to_align in unaligned_words:
        final_alignments.add((word_to_align, word_mapping.get(word_to_align)[0]))

    return sorted(final_alignments)



def project_dependencies(inst: Instance):
    pass

# -------------------------------------------
# Alignment Testcases
# -------------------------------------------
from unittest import TestCase
class MultipleAlignmentTests(TestCase):

    def test_many_to_many_alignments(self):
        multi_aln = [(0, 0.0), (0, 2.0), (1, 0.0), (1, 2.0), (1, 3.0), (2, 3.0), (3, 3.0)]
        tgt_aln = [(0, 0.0), (1, 2.0), (2, 3.0), (3, 3.0)]
        returned_alignments = handle_multiple_alignments(multi_aln)
        self.assertListEqual(tgt_aln, returned_alignments)

    def test_many_word_to_one_gloss(self):
        multi_aln = [(0,0.0), (1,0.0), (2, 0.0)]
        returned_alignments = handle_multiple_alignments(multi_aln)
        self.assertListEqual(multi_aln, returned_alignments)

    def test_one_word_to_many_gloss(self):
        multi_aln = [(0,0.0), (0,1.0), (0, 2.0)]
        returned_alignments = handle_multiple_alignments(multi_aln)
        self.assertListEqual(multi_aln, returned_alignments)

    def test_one_to_one_alignments(self):
        aln = [(0, 0.0), (1, 1.0), (2, 2.0)]
        returned_alignments = handle_multiple_alignments(aln)
        self.assertListEqual(aln, returned_alignments)

    def test_crossing_alignments(self):
        aln = [(0, 3.0), (2, 1.0), (2, 2.0), (4, 3.0)]
        self.assertListEqual(aln, handle_multiple_alignments(aln))

    def test_no_alignments(self):
        self.assertListEqual([], handle_multiple_alignments([]))

# -------------------------------------------
# Projection Cases
# -------------------------------------------

# NOUN > VERB > ADJ > ADV > PRON > DET > ADP > CONJ > PRT > NUM > PUNC > X
precedence = ['NOUN','VERB', 'ADJ', 'ADV', 'PRON', 'DET', 'ADP', 'CONJ', 'PRT', 'NUM', 'PUNC', 'X']

def project_pos(inst: Instance):
    """
    Project part-of-speech tags using the bilingual alignment.
    """
    # There must be alignments present to project
    assert inst.trans.alignments

    # Now, iterate over the translation words, and project their
    for trans_w in inst.trans:
        for aligned_gloss in trans_w.alignments: # type: SubWord

            # Check to see if the aligned gloss word already has
            # a part-of-speech tag, or if it does have one, that
            # it is a lower precedent than the proposed aligned tag.
            if (not aligned_gloss.word.pos or
                    precedence.index(aligned_gloss.word.pos) > precedence.index(trans_w.pos)):
                aligned_gloss.word.pos = trans_w.pos

    print(inst)
    print(inst.gloss)
    print([w.pos for w in inst.gloss])
    print(inst.trans)
    print([w.pos for w in inst.trans])
