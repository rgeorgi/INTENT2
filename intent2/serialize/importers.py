import sys
from collections import defaultdict

import xigt
import xigt.codecs.xigtxml
from xigt.model import Igt, Item
from intent2.xigt_helpers import xigt_find
from intent2.model import Word, GlossWord, TransWord, LangWord, SubWord, Phrase, TaggableMixin, Instance, Corpus
from intent2.utils.strings import morph_tokenize, clean_subword_string, word_tokenize

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
    words_tier = xigt_find(inst, id=LANG_WORD_ID)
    segmentation_tier = xigt_find(inst, segmentation=LANG_WORD_ID) or []

    if not words_tier:
        return Phrase(id=LANG_WORD_ID)

    return load_words(words_tier, segmentation_tier, id_to_object_mapping, WordType=LangWord)

def parse_gloss_tier(inst: Igt, id_to_object_mapping):
    """
    There

    :type inst: xigt.model.Igt
    """

    # Look for either a gloss tier (standard)
    # Or a gloss words tier (nonstandard)
    gloss_tier = xigt_find(inst, id='g')
    gloss_words_tier = xigt_find(inst, id='gw')

    # -- 1) If a gloss tier is found, use this
    #       to create word-level gloss items, since
    #       the segmentation is likely higher quality
    if gloss_tier:
        gloss_subwords = []
        word_groups = defaultdict(list)
        for gloss_item in gloss_tier:  # type: xigt.model.Item
            sw = SubWord(clean_subword_string(gloss_item.value()), id=gloss_item.id)
            if not sw.string.strip():
                raise Exception('Pre-segmented glosses in igt "{}" contains an empty token: "{}"'.format(inst.id, gloss_item.id))

            id_to_object_mapping[gloss_item.id] = sw
            gloss_subwords.append(sw)
            if gloss_item.alignment and id_to_object_mapping.get(gloss_item.alignment):
                aligned_item = id_to_object_mapping[gloss_item.alignment]
                sw.add_alignment(aligned_item)
                word_groups[aligned_item.word].append(sw)

        # Now, make gloss words by grouping the subwords
        gloss_words = []
        for aligned_word in word_groups.keys():
            w = GlossWord(subwords=word_groups[aligned_word])
            w.add_alignment(aligned_word)
            gloss_words.append(w)

    # -- 2) Otherwise, if a gloss_words tier was found,
    #       attempt to tokenize the morphemes.
    elif gloss_words_tier:
        gloss_words = []
        for gloss_word_item in gloss_words_tier: # type: xigt.model.Item
            subwords = [SubWord(clean_subword_string(g)) for g in morph_tokenize(gloss_word_item.value())]
            gw = GlossWord(subwords=subwords)
            id_to_object_mapping[gloss_word_item.id] = gw
            gloss_words.append(gw)

    else:
        return Phrase(id='gw')

    return Phrase(gloss_words, id='gw')

def load_words(tier, segmentation_tier, id_to_object_mapping, segment=True, WordType=Word):
    """
    :type tier: xigt.model.Tier
    :type segmentation_tier: xigt.model.Tier
    :type id_to_object_mapping: dict
    """

    # if there's no result for the supplied tier, return
    # an empty phrase.
    if not tier:
        return Phrase()

    # If there is no tier providing segmentation,
    # create the words tier based on that.
    words = []
    for xigt_word_item in tier:  # type: xigt.model.Item
        # If this word has segmentation in the morphs,
        # create it from there instead.
        if segmentation_tier:
            morph_segments = [morph for morph in segmentation_tier if morph.segmentation == xigt_word_item.id]
        else:
            morph_segments = []
        if morph_segments:
            morphs = []
            for xigt_subword in morph_segments:  # type: xigt.model.Item
                sw = SubWord(clean_subword_string(xigt_subword.value()), id=xigt_subword.id)
                id_to_object_mapping[xigt_subword.id] = sw

                if xigt_subword.alignment and id_to_object_mapping.get(xigt_subword.alignment):
                    sw.add_alignment(id_to_object_mapping.get(xigt_subword.alignment))

                morphs.append(sw)
            w = WordType(subwords=morphs, id='{}{}'.format(tier.id, len(words)+1))

        # Else if we want to segment the words
        elif segment:
            w = WordType(subwords=morph_tokenize(xigt_word_item.value()), id=xigt_word_item.id)
        else:
            w = WordType(xigt_word_item.value(), id=xigt_word_item.id)

        id_to_object_mapping[xigt_word_item.id] = w
        words.append(w)

    return Phrase(words)


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
        return load_words(trans_words_tier, None, id_to_object_mapping, WordType=TransWord)

    if not trans_tier:
        return Phrase(id='tw')
    elif len(trans_tier) > 1:
        # print(xigt.codecs.xigtxml.encode_igt(inst))
        sys.stderr.write('NOT IMPLEMENTED: Multiple Translations!\n')

    return Phrase([TransWord(s, id='{}{}'.format('tw', i+1))
                   for i, s in enumerate(word_tokenize(trans_tier[0].value()))],
                  id='tw')

def parse_pos(inst, pos_id, id_to_object_mapping):
    pos_tag_tier = xigt_find(inst, alignment=pos_id, type='pos') or []
    for pos_tag_item in pos_tag_tier:  # type: xigt.model.Item
        aligned_object = id_to_object_mapping.get(pos_tag_item.alignment) # type: TaggableMixin
        if aligned_object:
            aligned_object.pos = pos_tag_item.value()



# -------------------------------------------
# Now, parse into INTENT2 model
# -------------------------------------------
def parse_xigt_corpus(xigt_corpus):
    """
    :type xigt_corpus: xigt.model.XigtCorpus
    :rtype: Corpus
    """
    from intent2.model import Corpus
    return Corpus([parse_xigt_instance(xigt_inst) for xigt_inst in xigt_corpus])

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

import unittest
class segmentTests(unittest.TestCase):
    pass