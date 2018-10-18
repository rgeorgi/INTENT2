from collections import defaultdict

import xigt
import xigt.codecs.xigtxml
from intent2.xigt_helpers import xigt_find
from intent2.model import Word, SubWord, Phrase, TaggableMixin
from intent2.utils.strings import word_tokenize, clean_subword_string, phrase_tokenize

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
  </xigt-corpus>"""


def parse_words(inst, words_id, id_to_object_mapping):
    """
    Given a instance, find the specified word tier
    and return the words either made up of pre-provided
    segmentations from a tier that segments them,
    or try to create the segmentations with subword-level
    tokenization.

    :type inst: xigt.model.Igt
    :type words_id: str
    """
    words_tier = xigt_find(inst, id=words_id)
    segmentation_tier = xigt_find(inst, segmentation=words_id) or []
    words = []
    for xigt_word_item in words_tier:  # type: xigt.model.Item
        # If this word has segmentation in the morphs,
        # create it from there instead.
        morph_segments = [morph for morph in segmentation_tier if morph.segmentation == xigt_word_item.id]
        if morph_segments:
            morphs = []
            for morph in morph_segments: # type: xigt.model.Item
                sw = SubWord(clean_subword_string(morph.value()))
                id_to_object_mapping[morph.id] = sw
                morphs.append(sw)
            w = Word(subwords=morphs)
        else:
            w = Word(subwords=word_tokenize(xigt_word_item.value()))

        id_to_object_mapping[xigt_word_item.id] = w
        words.append(w)
    return words

def align_tiers(inst, align_to_id):
    """
    :type tier_1: xigt.model.Tier
    """
    align_to_tier = xigt_find(inst, id=align_to_id)  # type: xigt.model.Tier
    align_from_tier = xigt_find(inst, alignment=align_to_id)  #type: xigt.model.Tier

    for align_from_item in align_from_tier: # type: xigt.model.Item
        print(align_from_item.id, align_from_item.alignment)

def parse_gloss_tier(inst, id_to_object_mapping):
    gloss_tier = xigt_find(inst, id='g')
    gloss_words_tier = xigt_find(inst, id='gw')
    if gloss_tier:
        gloss_subwords = []
        word_groups = defaultdict(list)
        for gloss_item in gloss_tier:  # type: xigt.model.Item
            sw = SubWord(clean_subword_string(gloss_item.value()))
            id_to_object_mapping[gloss_item.id] = sw
            gloss_subwords.append(sw)
            if gloss_item.alignment and id_to_object_mapping.get(gloss_item.alignment):
                aligned_item = id_to_object_mapping[gloss_item.alignment]
                sw.add_alignment(aligned_item)
                word_groups[aligned_item.word].append(sw)

        # Now, make gloss words by grouping the subwords
        gloss_words = []
        for aligned_word in word_groups.keys():
            w = Word(subwords=word_groups[aligned_word])
            w.add_alignment(aligned_word)
            gloss_words.append(w)


    elif gloss_words_tier:
        gloss_words = []
        for gloss_word_item in gloss_words_tier: # type: xigt.model.Item
            subwords = [SubWord(clean_subword_string(g)) for g in word_tokenize(gloss_word_item.value())]
            gw = Word(subwords=subwords)
            id_to_object_mapping[gloss_word_item.id] = gw
            gloss_words.append(gw)

    return Phrase(gloss_words)






def parse_pos(inst, pos_id, id_to_object_mapping):
    pos_tag_tier = xigt_find(inst, alignment=pos_id, type='pos') or []
    for pos_tag_item in pos_tag_tier:  # type: xigt.model.Item
        aligned_object = id_to_object_mapping.get(pos_tag_item.alignment) # type: TaggableMixin
        if aligned_object:
            aligned_object.pos = pos_tag_item.value()

def parse_trans(inst):
    trans_tier = xigt_find(inst, type='translations')
    if len(trans_tier) > 1:
        raise Exception('NOT IMPLEMENTED: Multiple Translations!')

    return Phrase([Word(s) for s in phrase_tokenize(trans_tier[0].value())])


# -------------------------------------------
# Now, parse into INTENT2 model
# -------------------------------------------
def parse_xigt(inst):
    """
    :type inst: xigt.model.Igt
    """

    # Keep a mapping of the ID strings and their associated mappings
    id_to_object_mapping = {}

    # -- 1) Create the language phrase.
    lang_words = parse_words(inst, 'w', id_to_object_mapping)
    lang_p = Phrase(lang_words)
    gloss_p = parse_gloss_tier(inst, id_to_object_mapping)

    # print(repr(lang_p))
    # print(repr(gloss_p))
    parse_pos(inst, 'm', id_to_object_mapping)

    trans_p = parse_trans(inst)
    print(lang_p)
    print(gloss_p)
    print(trans_p)





if __name__ == '__main__':
    xc = xigt.codecs.xigtxml.loads(test_case_one)
    # parse_xigt(xc[0])
    parse_xigt(xc[1])
