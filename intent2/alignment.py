"""
Module to hold all the logic for heuristic alignment
"""

from intent2.model import Instance, Word
from intent2.processing import process_trans_if_needed, load_spacy
from typing import List, Tuple
from spacy.tokens import Token, Doc

# -------------------------------------------
# Set up logging
# -------------------------------------------
import logging
ALIGN_LOG = logging.getLogger('alignment')

# -------------------------------------------
# Gloss-to-morph alignment
# -------------------------------------------
def gloss_to_morph_align(inst: Instance):
    """
    Given an instance, make sure that the glosses are aligned
    to the language line morphemes correctly.
    """
    assert inst.lang and inst.gloss

    lang_sw = list(inst.lang.subwords)
    gloss_sw = list(inst.gloss.subwords)

    if len(lang_sw) != len(gloss_sw):
        raise Exception('Number of morphs and glosses differ.')

    for i, gloss in enumerate(inst.gloss.subwords):
        gloss.add_alignment(lang_sw[i])


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
            'art': ['the'],
            '3pl': ['they'],
            '3sg': ['he', 'she', 'him', 'her'],
            '3sgf': ['she', 'her'],
            '3fsg': ['she', 'her'],
            '2sg': ['you'],
            '3sgp': ['he'],
            'poss': ['his', 'her', 'my', 'their'],
            'neg': ["n't", 'not'],
            '2pl': ['you']}

class AlignException(Exception): pass

def heuristic_alignment(inst: Instance, heur_list = None):
    """
    Implement the alignment between words

    :type inst: Instance
    """
    ALIGN_LOG.info('Attempting heuristic alignment for instance "{}"'.format(inst.id))

    # To do heuristic alignment, we need minimally a gloss and translation line.
    if not (inst.gloss and inst.trans and inst.lang):
        raise AlignException('Instance "{}" does not contain L,G,T lines.'.format(inst.id))

    # We also need the
    if not (len(inst.lang) == len(inst.gloss)):
        raise AlignException('Instance "{}" has different number of L, G tokens.'.format(inst.id))

    # We also need the translation line to have been processed for things like POS
    # tags and lemmas.
    process_trans_if_needed(inst)

    ALIGN_LOG.info('Removing previous alignments, if present.')
    for trans_w in inst.trans:
        for alignment in list(trans_w.alignments):
            trans_w.remove_alignment(alignment)

    # We don't need to store the sub-sub-word information that we will use to perform
    # alignment, but we want to get things like the lemmas and vector representations
    # of the period-separated portions, so let's get those here.
    gloss_parts = []
    for gloss_w in inst.gloss:
        gloss_parts.extend(gloss_w.subword_parts)

    spacy_eng = load_spacy()
    gloss_part_doc = Doc(spacy_eng.vocab, words=[part[1] for part in gloss_parts])
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
            assert trans_w.index is not None
            if lang_w.string.lower() == trans_w.string.lower():
                existing_alignments.add((trans_w.index, lang_w.index))
                existing_alignments = set(handle_multiple_alignments(existing_alignments))

    # The "heur_list" is the list defining which, and the
    # order of which heuristics to use for alignment.
    if heur_list is None:
        heur_list = ['exact', 'lemma', 'gram']

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


def get_alignment_words(alignments: List[Tuple[int, float]]):
    return {word_index for word_index, gloss_index in alignments}

def get_alignment_glosses(alignments: List[Tuple[int, float]]):
    return {gloss_index for word_index, gloss_index in alignments}

def remove_conflicting_alignments(existing_alignments: List[Tuple[int, float]],
                                  new_alignments: List[Tuple[int, float]],
                                  allow_multiple_alignments=True):
    """
    Remove any newly proposed alignments that overlap with already
    assigned alignments
    """
    aligned_words = get_alignment_words(existing_alignments)
    aligned_glosses = get_alignment_glosses(existing_alignments)

    def num_alignments(src_index, type='word'):
        index = 0 if type=='word' else 1
        return len([aln for aln in new_alignments if aln[index] == src_index])

    # -------------------------------------------
    # There are two cases in which we want to align two tokens:
    #   1) Neither token has an alignment.
    #   2) One token is already aligned, but a newly proposed candidate for
    #      alignment has only one option AND we want to allow multiple
    #      alignments to be proposed with this heuristic.
    returned_alignments = []
    for word_index, gloss_index in new_alignments:
        align=False
        if word_index not in aligned_words and gloss_index not in aligned_glosses:
            ALIGN_LOG.debug('No alignments for pair ({},{}). Adding.'.format(word_index, gloss_index))
            align=True
        elif word_index not in aligned_words and num_alignments(word_index) == 1:
            ALIGN_LOG.debug('Alignment exists for gloss {1}, but word {0} has no other candidates. Alinging ({0},{1}).'.format(
                word_index, gloss_index))
            align=True
        elif gloss_index not in aligned_glosses and num_alignments(gloss_index) == 1:
            ALIGN_LOG.debug('Alignment exists for word {0}, but gloss {1} has no other candidates. Aligning ({0},{1})'.format(
                word_index, gloss_index))
            align=True
        if align:
            returned_alignments.append((word_index, gloss_index))

    return returned_alignments


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