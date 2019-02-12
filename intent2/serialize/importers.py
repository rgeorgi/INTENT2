import sys
from collections import defaultdict

import xigt
import xigt.codecs.xigtxml
from xigt.model import Igt, Item
from intent2.xigt_helpers import xigt_find
from intent2.model import Word, GlossWord, TransWord, LangWord, SubWord, Phrase, TaggableMixin, Instance, Corpus
from intent2.utils.strings import morph_tokenize, subword_str_to_subword, word_tokenize, word_str_to_subwords

from typing import Union

import logging
IMPORT_LOG = logging.getLogger()

# -------------------------------------------
# Test Cases
# -------------------------------------------

test_case_one = """
<xigt-corpus>
  <igt id="igt20110518AbuiTakalelangFD02_0003" corpus-id="2011.SurreyStimuli">
    <tier id="p" type="phrases" content="n">
      <item id="p1" content="n1">la heteitu yo!</item>
    </tier>
    <tier id="w" type="words" segmentation="p">
      <item id="w1" segmentation="p1">la</item>
      <item id="w2" segmentation="p1">heteitu</item>
      <item id="w3" segmentation="p1">yo!</item>
    </tier>
    <tier id="m" type="morphemes" segmentation="w">
      <item id="m1" segmentation="w1">la</item>
      <item id="m2" segmentation="w2">he-</item>
      <item id="m3" segmentation="w2">teitu</item>
      <item id="m4" segmentation="w3">yo</item>
    </tier>
    <tier id="g" type="glosses" alignment="m">
      <item id="g1" alignment="m1">be.Md</item>
      <item id="g2" alignment="m2">3.loc-</item>
      <item id="g3" alignment="m3">first</item>
      <item id="g4" alignment="m4">Md.ad</item>
    </tier>
    <tier id="pos" type="pos" alignment="m">
      <item id="pos1" alignment="m1">vi</item>
      <item id="pos2" alignment="m2">pro-</item>
      <item id="pos3" alignment="m3">num</item>
      <item id="pos4" alignment="m4">dem</item>
    </tier>
    <tier id="t" type="translations" alignment="p" content="n">
      <item id="t1" alignment="p1" content="n3">the first one</item>
    </tier>
    <tier id="n" type="odin" state="normalized">
      <item id="n1" tag="L">la heteitu yo!</item>
      <item id="n2" tag="G"> be.Md 3.loc-first Md.ad</item>
      <item id="n3" tag="T">the first one</item>
    </tier>
  </igt>
  <igt id="ii1">
    <metadata type="intent-meta">
      <meta type="language" iso-639-3="eng" name="english" tiers="glosses translations" />
    </metadata>
    <tier id="r" type="odin" state="raw">
      <item id="r1" tag="L">Peo-Ø Goyo-ta tuuka kaba'i-ta etbwa-k-tia-Ø .</item>
      <item id="r2" tag="G">Peo-NOM Goyo-ACC yesterday horse-ACC steal-PRFV-SAY-PRES .</item>
      <item id="r3" tag="T">Pedro says Goyo have stolen the horse yesterday .</item>
    </tier>
    <tier id="c" type="odin" alignment="r" state="cleaned">
      <item id="c1" alignment="r1" tag="L">Peo-Ø Goyo-ta tuuka kaba'i-ta etbwa-k-tia-Ø .</item>
      <item id="c2" alignment="r2" tag="G">Peo-NOM Goyo-ACC yesterday horse-ACC steal-PRFV-SAY-PRES .</item>
      <item id="c3" alignment="r3" tag="T">Pedro says Goyo have stolen the horse yesterday .</item>
    </tier>
    <tier id="n" type="odin" alignment="c" state="normalized">
      <item id="n1" alignment="c1" tag="L">Peo-Ø Goyo-ta tuuka kaba'i-ta etbwa-k-tia-Ø .</item>
      <item id="n2" alignment="c2" tag="G">Peo-NOM Goyo-ACC yesterday horse-ACC steal-PRFV-SAY-PRES .</item>
      <item id="n3" alignment="c3" tag="T">Pedro says Goyo have stolen the horse yesterday .</item>
    </tier>
    <tier id="p" type="phrases" content="n">
      <item id="p1" content="n1" />
    </tier>
    <tier id="w" type="words" segmentation="p">
      <item id="w1" segmentation="p1[0:5]" />
      <item id="w2" segmentation="p1[6:13]" />
      <item id="w3" segmentation="p1[14:19]" />
      <item id="w4" segmentation="p1[20:29]" />
      <item id="w5" segmentation="p1[30:43]" />
      <item id="w6" segmentation="p1[44:45]" />
    </tier>
    <tier id="w-ds" type="dependencies" dep="w" head="w">
      <metadata type="intent-meta">
        <meta type="data-provenance" date="2015-10-09 21:42:51-UTC" method="supervised" source="intent" />
      </metadata>
      <item id="w-ds1" dep="w5" />
      <item id="w-ds2" dep="w1" head="w5" />
      <item id="w-ds3" dep="w2" head="w5" />
      <item id="w-ds4" dep="w3" head="w5" />
      <item id="w-ds5" dep="w4" head="w5" />
      <item id="w-ds6" dep="w6" head="w5" />
    </tier>
    <tier id="t" type="translations" alignment="p" content="n">
      <item id="t1" alignment="p1" content="n3" />
    </tier>
    <tier id="tw" type="words" segmentation="t">
      <item id="tw1" segmentation="t1[0:5]" />
      <item id="tw2" segmentation="t1[6:10]" />
      <item id="tw3" segmentation="t1[11:15]" />
      <item id="tw4" segmentation="t1[16:20]" />
      <item id="tw5" segmentation="t1[21:27]" />
      <item id="tw6" segmentation="t1[28:31]" />
      <item id="tw7" segmentation="t1[32:37]" />
      <item id="tw8" segmentation="t1[38:47]" />
      <item id="tw9" segmentation="t1[48:49]" />
    </tier>
    <tier id="tw-ds" type="dependencies" dep="tw" head="tw">
      <metadata type="intent-meta">
        <meta type="data-provenance" date="2015-10-09 21:42:51-UTC" method="supervised" source="intent" />
      </metadata>
      <item id="tw-ds1" dep="tw2" />
      <item id="tw-ds2" dep="tw1" head="tw2" />
      <item id="tw-ds3" dep="tw5" head="tw2" />
      <item id="tw-ds4" dep="tw3" head="tw5" />
      <item id="tw-ds5" dep="tw4" head="tw5" />
      <item id="tw-ds6" dep="tw7" head="tw5" />
      <item id="tw-ds7" dep="tw6" head="tw7" />
      <item id="tw-ds8" dep="tw8" head="tw5" />
      <item id="tw-ds9" dep="tw9" head="tw2" />
    </tier>
    <tier id="gw" type="glosses" content="n">
      <metadata type="intent-meta">
        <meta type="extended-data" date="2015-10-09 21:42:51-UTC" token-type="word" />
      </metadata>
      <item id="gw1" content="n2[0:7]" />
      <item id="gw2" content="n2[8:16]" />
      <item id="gw3" content="n2[17:26]" />
      <item id="gw4" content="n2[27:36]" />
      <item id="gw5" content="n2[37:56]" />
      <item id="gw6" content="n2[57:58]" />
    </tier>
    <tier id="a" type="bilingual-alignments" source="tw" target="gw">
      <metadata type="intent-meta">
        <meta type="data-provenance" date="2015-10-09 21:42:51-UTC" method="manual" source="intent" />
      </metadata>
      <item id="a1" source="tw1" target="gw1" />
      <item id="a2" source="tw2" target="gw5" />
      <item id="a3" source="tw3" target="gw2" />
      <item id="a4" source="tw5" target="gw5" />
      <item id="a5" source="tw7" target="gw4" />
      <item id="a6" source="tw8" target="gw3" />
      <item id="a7" source="tw9" target="gw6" />
    </tier>
  </igt>
  <igt id="igt20030701TifolafengBapakAnde1_0002" corpus-id="2003.Agricultural.Year.AP">
    <tier id="p" type="phrases" content="n">
      <item id="p1" content="n1">ni,**hash** iya ba heyeting-ayoku ni yaa,**hash** pun namei.</item>
    </tier>
    <tier id="w" type="words" segmentation="p">
      <item id="w1" segmentation="p1">ni</item>
      <item id="w2" segmentation="p1">iya</item>
      <item id="w3" segmentation="p1">ba</item>
      <item id="w4" segmentation="p1">heyeting-ayoku</item>
      <item id="w5" segmentation="p1">ni</item>
      <item id="w6" segmentation="p1">yaa</item>
      <item id="w7" segmentation="p1">pun</item>
      <item id="w8" segmentation="p1">namei.</item>
    </tier>
    <tier id="m" type="morphemes" segmentation="w">
      <item id="m1" segmentation="w1">ni</item>
      <item id="m2" segmentation="w2">iya</item>
      <item id="m3" segmentation="w3">ba</item>
      <item id="m4" segmentation="w4">he-</item>
      <item id="m5" segmentation="w4">yeting-ayoku</item>
      <item id="m6" segmentation="w5">ni</item>
      <item id="m7" segmentation="w6">yaa</item>
      <item id="m8" segmentation="w7">pun</item>
      <item id="m9" segmentation="w8">namei</item>
    </tier>
    <tier id="g" type="glosses" alignment="m">
      <item id="g1" alignment="m1">1pl.excl.agt</item>
      <item id="g2" alignment="m2">moon</item>
      <item id="g3" alignment="m3">Sim</item>
      <item id="g4" alignment="m4">ORD-</item>
      <item id="g5" alignment="m5">seven</item>
      <item id="g6" alignment="m6">1pl.excl.agt</item>
      <item id="g7" alignment="m7">go</item>
      <item id="g8" alignment="m8">field</item>
      <item id="g9" alignment="m9">prepare.field</item>
    </tier>
    <tier id="pos" type="pos" alignment="m">
      <item id="pos1" alignment="m1">pro</item>
      <item id="pos2" alignment="m2">n</item>
      <item id="pos3" alignment="m3">conj</item>
      <item id="pos4" alignment="m4">num.pref-</item>
      <item id="pos5" alignment="m5">num</item>
      <item id="pos6" alignment="m6">pro</item>
      <item id="pos7" alignment="m7">v.0</item>
      <item id="pos8" alignment="m8">n</item>
      <item id="pos9" alignment="m9">v.0</item>
    </tier>
    <tier id="t" type="translations" alignment="p" content="n">
      <item id="t1" alignment="p1" content="n3">in the seventh month (in July) we go to work in the fields</item>
    </tier>
    <tier id="n" type="odin" state="normalized">
      <item id="n1" tag="L">ni,**hash** iya ba heyeting-ayoku ni yaa,**hash** pun namei.</item>
      <item id="n2" tag="G"> 1pl.excl.agt moon Sim ORD-seven 1pl.excl.agt go field prepare.field</item>
      <item id="n3" tag="T">in the seventh month (in July) we go to work in the fields</item>
    </tier>
  </igt>
  </xigt-corpus>"""

class ImportException(Exception): pass
class SegmentationTierException(ImportException): pass


# -------------------------------------------
# Read in Language, Gloss, Translation
# -------------------------------------------

from .consts import *

def parse_lang_tier(inst, id_to_object_mapping):
    """
    Given a instance, find the specified word tier
    and return the words either made up of pre-provided
    segmentations from a tier that segments them,
    or try to create the segmentations with subword-level
    tokenization.

    :type inst: xigt.model.Igt
    :type words_id: str
    """
    lang_tier = xigt_find(inst, id=LANG_WORD_ID)
    morph_tier = xigt_find(inst, segmentation=LANG_WORD_ID)

    if not lang_tier:
        return Phrase(id_=LANG_WORD_ID)

    return load_words(id_to_object_mapping,
                      words_tier=lang_tier,
                      segmentation_tier=morph_tier,
                      WordType=LangWord)


def parse_gloss_tier(inst: Igt, id_to_object_mapping):
    """
    The load_words tier assumes that

    :type inst: xigt.model.Igt
    """
    # Look for either a gloss tier (standard)
    # Or a gloss words tier (nonstandard)
    gloss_tier = xigt_find(inst, id='g')
    gloss_words_tier = xigt_find(inst, id='gw')
    lang_words_tier = xigt_find(inst, id='w')

    gloss_p = load_words(id_to_object_mapping,
                         words_tier=gloss_words_tier,
                         segmentation_tier=gloss_tier,
                         alignment_tier=lang_words_tier,
                         WordType=GlossWord)

    gloss_p._id = 'gw'

    return gloss_p

def item_id(base_str, n):
    """
    Adds modularity to creating item IDs
    :param base_str:
    :param n:
    :return:
    """
    return '{}{}'.format(base_str, n)

def create_phrase_from_words_tier(tier: xigt.model.Tier,
                                  do_segmentation: bool=True,
                                  WordType=Word):
    """
    Given a tier without pre-provided segmentation, return a phrase

    :param tier:
    :param id_to_object_mapping:
    :param WordType:
    :return:
    """
    def word_func(xigt_word_item):
        if do_segmentation:
            w = WordType(subwords=word_str_to_subwords(xigt_word_item.value()),
                         id=xigt_word_item.id)
        else:
            w = WordType(xigt_word_item.value(),
                         id=xigt_word_item.id)
        return w

    return Phrase([word_func(xw) for xw in tier])



def create_phrase_from_segments_alignments(id_to_object_mapping,
                                           segmentation_tier: xigt.model.Tier,
                                           aligned_tier: xigt.model.Tier,
                                           WordType=Word):
    """
    Create a phrase by using a segmentation tier and the word-level groupings
    provided by the tier with which it is aligned.

    This is useful in the case of glosses which align with morphemes, but
    are not given their own word-level groupings in the data.
    """
    # -- 0) Keep a mapping of word-level groups, and
    #       the subword items that they contain.
    word_to_segment_map = defaultdict(list)

    # -- 1) Iterate over the segmented objects, and
    #       add them to the group map.
    for segment_item in segmentation_tier:  # type: xigt.model.Item
        subword_obj = subword_str_to_subword(segment_item.value(), id_=segment_item.id)

        # TODO: What about the case where we have a free-floating hyphen?
        if not subword_obj.string.strip():
            raise ImportException(
                'Pre-segmented glosses in igt "{}" contains an empty token: "{}"'.format(segmentation_tier.igt.id,
                                                                                         segment_item.id))

        # Enter the subword obj into the mapping dict.
        id_to_object_mapping[segment_item.id] = subword_obj

        # We assume that there are alignments for every segmentation object,
        # and that
        if not (segment_item.alignment and id_to_object_mapping.get(segment_item.alignment)):
            raise ImportException('Item "{}" in tier "{}" for instance "{}" missing alignment target "{}"'.format(
                segment_item.id,
                segmentation_tier.id,
                segmentation_tier.igt.id,
                segment_item.alignment
            ))
        aligned_obj = id_to_object_mapping[segment_item.alignment] # type: Union[SubWord, Word]
        subword_obj.add_alignment(aligned_obj)

        aligned_word = aligned_obj if isinstance(aligned_obj, Word) else aligned_obj.word

        word_to_segment_map[aligned_word].append(subword_obj)

    # -- 2) Check that our group map contains the same number of groups as
    #       there exist in the aligned tier.
    assert len(aligned_tier) == len(word_to_segment_map)

    # -- 3) Now, create words based on the groupings provided by the
    #       group map.
    word_groups = sorted(word_to_segment_map.keys(), key=lambda word: word.index)
    phrase = Phrase()
    for aligned_word in word_groups:  # type: Word
        new_word = WordType(subwords=word_to_segment_map[aligned_word],
                      id_=item_id('gw', aligned_word.index))
        new_word.add_alignment(aligned_word)
        phrase.add_word(new_word)
    return phrase



def load_words(id_to_object_mapping,
               words_tier=None, segmentation_tier=None, alignment_tier=None,
               do_segmentation=True, WordType=Word):
    """
    Given a words tier (tier) and tier that provides segmentation for that tier, but which
    may be None (segmentation_tier), return a phrase with those words/subwords.

    There are
        A. A words tier and segmentation tier exist
            - Use segmentation tier, check segmentation exists for all words.
        B. A words tier exists, but no segmentation tier
            - Segment the words tier.
        C. No words tier exists, a segmentation tier is aligned with a tier that has words.
            - Group the segments according to the aligned words.
        D. No words tier exists, no segmentation tier exists.
            - Return an empty phrase

    :rtype: Phrase
    """

    # -- C / D) No words tier exists...
    if not words_tier:
        if segmentation_tier:
            assert alignment_tier
            IMPORT_LOG.info('Creating words tier from combination of segmentation "{}" and aligned tier "{}"'.format(
                segmentation_tier.id, alignment_tier.id
            ))
            return create_phrase_from_segments_alignments(id_to_object_mapping,
                                                          segmentation_tier,
                                                          alignment_tier,
                                                          WordType)
        else:
            return Phrase()

    # -- B) If there's not a segmentation tier, return the phrase
    #       created by the words tier alone.
    elif not segmentation_tier:
        return create_phrase_from_words_tier(words_tier,
                                             do_segmentation=do_segmentation,
                                             WordType=WordType)

    # -- A) If there is both a words tier and segmentation tier,
    #       use the segmentation provided by the segmentation tier.
    elif segmentation_tier and words_tier:
        words = []

        # For each word in the tier, retrieve the portions of the word
        # that are given as segments
        for xigt_word_item in words_tier:  # type: xigt.model.Item
            morph_segments = [morph for morph in segmentation_tier
                              if morph.segmentation == xigt_word_item.id]

            # If the segmentation tier is provided,
            # we assume that every word has some form
            # of segmentation.
            if not morph_segments:
                raise SegmentationTierException('Segmentation tier provided for instance "{}", but no segments for word "{}"'.format(words_tier.igt.id,

                                                                                                                   xigt_word_item.id))
            else:
                morphs = []
                for xigt_subword in morph_segments:  # type: xigt.model.Item

                    # TODO: What if there is a bare "-" here? Should probably attach to the left or right.
                    sw = subword_str_to_subword(xigt_subword.value(), id_=xigt_subword.id)
                    id_to_object_mapping[xigt_subword.id] = sw

                    if xigt_subword.alignment and id_to_object_mapping.get(xigt_subword.alignment):
                        sw.add_alignment(id_to_object_mapping.get(xigt_subword.alignment))

                    morphs.append(sw)
                w = WordType(subwords=morphs,
                             id_=item_id(words_tier.id, len(words)+1))



            id_to_object_mapping[xigt_word_item.id] = w
            words.append(w)

        return Phrase(words)
    else:
        raise ImportException("Unable to create phrase.")




def parse_trans_tier(inst, id_to_object_mapping):
    """
    Parse the translation tier

    :type id_to_object_mapping: dict
    :type inst: xigt.model.Igt
    """
    trans_tier = xigt_find(inst, type='translations')

    # If there's a translations words tier, use that.
    trans_words_tier = xigt_find(inst, segmentation='t', type='words')
    if trans_words_tier:
        IMPORT_LOG.debug("trans-words tier found.")
        return load_words(id_to_object_mapping,
                          words_tier=trans_words_tier,
                          WordType=TransWord)

    if not trans_tier:
        return None
    elif len(trans_tier) > 1:
        raise ImportException('NOT IMPLEMENTED: Multiple Translations!')
    elif trans_tier[0].value() is None:
        return None

    # Otherwise, tokenize the words on the translation tier and create a
    # new phrase.
    trans_phrase = Phrase(id_='tw')
    trans_tier_str = trans_tier[0].value()
    IMPORT_LOG.debug('No trans-word tier found for instance "{}", tokenizing trans phrase: "{}"'.format(inst.id, trans_tier_str))
    for i, word in enumerate(word_tokenize(trans_tier_str)):
        trans_phrase.append(TransWord(word,
                                      id_=item_id('tw', i+1)))
    return trans_phrase

def parse_pos(inst, pos_id, id_to_object_mapping):
    pos_tag_tier = xigt_find(inst, alignment=pos_id, type='pos') or []
    for pos_tag_item in pos_tag_tier:  # type: xigt.model.Item
        aligned_object = id_to_object_mapping.get(pos_tag_item.alignment) # type: TaggableMixin
        if aligned_object:
            aligned_object.pos = pos_tag_item.value()



# -------------------------------------------
# Now, parse into INTENT2 model
# -------------------------------------------
def parse_xigt_corpus(xigt_corpus, ignore_import_errors=True):
    """
    :type xigt_corpus: xigt.model.XigtCorpus
    :rtype: Corpus
    """
    from intent2.model import Corpus

    instances = []
    for xigt_inst in xigt_corpus:
        try:
            intent_inst = parse_xigt_instance(xigt_inst)
            instances.append(intent_inst)
        except ImportException as ie:
            IMPORT_LOG.error('There was an error importing instance "{}": {}'.format(xigt_inst.id, ie))
            if not ignore_import_errors:
                raise ie

    return Corpus(instances)

def parse_odin(xigt_inst, tag, WordType=Word):
    """
    Look for the normalized ODIN tier of the given
    tag type, and convert it to words/subwords objects.

    :type xigt_inst: xigt.model.Igt
    """
    normalized_tier = xigt_find(xigt_inst, type="odin", attributes={'state':'normalized'})
    if normalized_tier:
        normalized_line = xigt_find(normalized_tier, tag=tag.upper())
        if normalized_line and normalized_line.value(): # type: xigt.model.Item
            words = [WordType(subwords=morph_tokenize(w)) for w in word_tokenize(normalized_line.value())]
            return Phrase(words)

    return Phrase()

def parse_bilingual_alignments(xigt_inst: Igt,
                               id_to_object_mapping: dict):
    """
    Retrieve any bilingual-alignment tier already existing in the instance,
    and add those alignments to our data model.

    :param xigt_inst: Source IGT Instance
    :param id_to_object_mapping: Mapping containing id strings that are seen
                                 in the xigt data, and the INTENT2 objects they map to.
    """
    align_tier = xigt_find(xigt_inst, type='bilingual-alignments')
    if align_tier:
        IMPORT_LOG.info("Alignment tier found. Importing original alignments.")
        for align_item in align_tier: # type: Item
            src_id = align_item.attributes.get('source')
            tgt_id = align_item.attributes.get('target')

            src_obj = id_to_object_mapping.get(src_id) # type: Union[Word,SubWord]
            tgt_obj = id_to_object_mapping.get(tgt_id) # type: Union[Word,SubWord]

            if src_obj and tgt_obj:
                IMPORT_LOG.debug('Importing alignment of {}\u2b64{}'.format(repr(src_obj), repr(tgt_obj)))
                src_obj.add_alignment(tgt_obj)
            if not src_obj:
                IMPORT_LOG.debug('Alignment import issue: ID "{}" was not found.'.format(src_obj))
            if not tgt_obj:
                IMPORT_LOG.debug('Alignment import issue: ID "{}" was not found.'.format(src_obj))



def parse_xigt_instance(xigt_inst: Igt):
    """
    Given a Xigt instance, parse it into the INTENT2 objects
    for processing.

    Namely, the expected Xigt format requires:
       * a type="words" tier for the source language.
       * a type="glosses" tier that is aligned with the words tier
       * a type="translations" tier that provides translations

    :type xigt_inst: xigt.model.Igt
    """

    # Keep a mapping of the ID strings and their associated mappings
    id_to_object_mapping = {}

    def process_tier_or_odin(func, odin_tag, WordType):
        """
        Attempt to parse
        """
        try:
            phrase = func(xigt_inst, id_to_object_mapping)
            if not phrase:
                return parse_odin(xigt_inst, odin_tag, WordType)
        except AssertionError as ae:
            IMPORT_LOG.error("Error parsing instance {}: {}".format(xigt_inst.id, ae))
            phrase = None
        return phrase


    # -- 1a) Create the language phrase
    lang_p = process_tier_or_odin(parse_lang_tier, 'L', LangWord)

    # -- 1b) Create the gloss phrase
    gloss_p = process_tier_or_odin(parse_gloss_tier, 'G', GlossWord)

    # -- 1c) Create the translation phrase
    trans_p = process_tier_or_odin(parse_trans_tier, 'T', TransWord)

    # -- 2) Add any POS tags found.
    parse_pos(xigt_inst, 'm', id_to_object_mapping)
    parse_pos(xigt_inst, 'w', id_to_object_mapping)

    parse_bilingual_alignments(xigt_inst, id_to_object_mapping)

    inst = Instance(lang_p, gloss_p, trans_p, id=xigt_inst.id)
    return inst


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument('xc')

    args = p.parse_args()

    inst = xigt.codecs.xigtxml.loads('''<xigt-corpus><igt id="igt20030701TifolafengBapakAnde1_0002" corpus-id="2003.Agricultural.Year.AP">
  <tier id="p" type="phrases" content="n">
    <item id="p1" content="n1">ni,**hash** iya ba heyeting-ayoku ni yaa,**hash** pun namei.</item>
  </tier>
  <tier id="w" type="words" segmentation="p">
    <item id="w1" segmentation="p1">ni</item>
    <item id="w2" segmentation="p1">iya</item>
    <item id="w3" segmentation="p1">ba</item>
    <item id="w4" segmentation="p1">heyeting-ayoku</item>
    <item id="w5" segmentation="p1">ni</item>
    <item id="w6" segmentation="p1">yaa</item>
    <item id="w7" segmentation="p1">pun</item>
    <item id="w8" segmentation="p1">namei.</item>
  </tier>
  <tier id="m" type="morphemes" segmentation="w">
    <item id="m1" segmentation="w1">ni</item>
    <item id="m2" segmentation="w2">iya</item>
    <item id="m3" segmentation="w3">ba</item>
    <item id="m4" segmentation="w4">he-</item>
    <item id="m5" segmentation="w4">yeting-ayoku</item>
    <item id="m6" segmentation="w5">ni</item>
    <item id="m7" segmentation="w6">yaa</item>
    <item id="m8" segmentation="w7">pun</item>
    <item id="m9" segmentation="w8">namei</item>
  </tier>
  <tier id="g" type="glosses" alignment="m">
    <item id="g1" alignment="m1">1pl.excl.agt</item>
    <item id="g2" alignment="m2">moon</item>
    <item id="g3" alignment="m3">Sim</item>
    <item id="g4" alignment="m4">ORD-</item>
    <item id="g5" alignment="m5">seven</item>
    <item id="g6" alignment="m6">1pl.excl.agt</item>
    <item id="g7" alignment="m7">go</item>
    <item id="g8" alignment="m8">field</item>
    <item id="g9" alignment="m9">prepare.field</item>
  </tier>
  <tier id="pos" type="pos" alignment="m">
    <item id="pos1" alignment="m1">pro</item>
    <item id="pos2" alignment="m2">n</item>
    <item id="pos3" alignment="m3">conj</item>
    <item id="pos4" alignment="m4">num.pref-</item>
    <item id="pos5" alignment="m5">num</item>
    <item id="pos6" alignment="m6">pro</item>
    <item id="pos7" alignment="m7">v.0</item>
    <item id="pos8" alignment="m8">n</item>
    <item id="pos9" alignment="m9">v.0</item>
  </tier>
  <tier id="t" type="translations" alignment="p" content="n">
    <item id="t1" alignment="p1" content="n3">in the seventh month (in July) we go to work in the fields</item>
  </tier>
  <tier id="n" type="odin" state="normalized">
    <item id="n1" tag="L">ni,**hash** iya ba heyeting-ayoku ni yaa,**hash** pun namei.</item>
    <item id="n2" tag="G"> 1pl.excl.agt moon Sim ORD-seven 1pl.excl.agt go field prepare.field</item>
    <item id="n3" tag="T">in the seventh month (in July) we go to work in the fields</item>
  </tier>
</igt></xigt-corpus>''')[0]
    i = parse_xigt_instance(inst)
    print(repr(i.lang))

    # with open(args.xc, 'r') as f:
    #     xc = xigt.codecs.xigtxml.load(f)
    #     inst = xc[0]
    #     print(xigt.codecs.xigtxml.encode_igt(inst))
    #     print(parse_xigt(inst))

