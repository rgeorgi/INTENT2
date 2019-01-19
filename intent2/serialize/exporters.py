import re

from intent2.model import Instance, Corpus, Phrase, IdMixin, Word, SubWord
from xigt.model import XigtCorpus, Igt, Tier, Item
from xigt.codecs.xigtxml import dumps
from typing import Iterable, Tuple, Union, List

def corpus_to_xigt(corp: Corpus):
    xc = XigtCorpus()
    for inst in corp.instances:
        inst = instance_to_xigt(inst)
        xc.append(inst)
    print(dumps(xc))

PHRASE_KEY = 'phrase'
WORDS_KEY = 'words'
SUBWORDS_KEY = 'subwords'
LANG_KEY = 'lang'
GLOSS_KEY = 'gloss'
TRANS_KEY = 'trans'
TYPE_KEY = 'type'
ID_KEY = 'id'
SEG_KEY = 'segmentation'
ALN_KEY = 'alignment'

xigt_conventions = {LANG_KEY:{PHRASE_KEY: {TYPE_KEY:'phrases', ID_KEY:'p'},
                              WORDS_KEY: {TYPE_KEY:'words', ID_KEY:'w', SEG_KEY:'p'},
                              SUBWORDS_KEY: {TYPE_KEY:'morphemes', ID_KEY:'m', SEG_KEY:'w'}},
                    GLOSS_KEY:{SUBWORDS_KEY: {TYPE_KEY:'glosses', ID_KEY:'g', ALN_KEY:'m'}},
                    TRANS_KEY:{PHRASE_KEY: {TYPE_KEY:'translations', ID_KEY:'t'},
                               WORDS_KEY: {TYPE_KEY:'words', ID_KEY:'tw', SEG_KEY:'t'}
                               }
                    }


def get_xigt_str(key_sequence: List[str]):
    d = xigt_conventions
    while key_sequence:
        key = key_sequence.pop(0)
        if isinstance(d.get(key), dict):
            d = d.get(key)
        else:
            return d.get(key)
    return d


def tier_to_xigt(igt: Igt,
                 phrase: Phrase,
                 phrase_type: str):
    """
    Convert a tier to an IGT form.
    """
    # -- 1) Create phrase tier if expected.
    phrase_dict = get_xigt_str([phrase_type, PHRASE_KEY])
    if phrase_dict:
        phrase_tier = Tier(type=phrase_dict[TYPE_KEY],
                           id=phrase_dict[ID_KEY],
                           items=[Item(id=phrase_dict[ID_KEY]+'1',
                                       text=phrase.hyphenated)])
        igt.append(phrase_tier)


    # -- 1a) Create the word tier and associated POS tier.
    word_dict = get_xigt_str([phrase_type, WORDS_KEY])
    if word_dict:
        word_tier = Tier(type=word_dict[TYPE_KEY],
                         id=word_dict[ID_KEY],
                         segmentation=word_dict[SEG_KEY])
        word_pos_tier = Tier(type='pos',
                             alignment=word_dict[ID_KEY],
                             id='{}pos'.format(word_dict[ID_KEY]))

    # -- 1b) Create the subword tier. (Only add segmentation
    #        if we're also creating a word tier; e.g. lang, not gloss)
    sw_dict = get_xigt_str([phrase_type, SUBWORDS_KEY])
    if sw_dict:
        subword_tier = Tier(type=sw_dict[TYPE_KEY], id=sw_dict[ID_KEY])
        if word_dict:
            subword_tier.segmentation = word_dict[ID_KEY]
        subword_pos_tier = Tier(type='pos',
                                alignment=sw_dict[ID_KEY],
                                id='{}pos'.format(sw_dict[ID_KEY]))

    # Function to add POS tokens to the respective
    # pos tier when post ags are present.
    def add_to_pos_tier(token: Union[Word, SubWord],
                        token_id: str,
                        tier: Tier):
        if token.pos:
            token_pos_item = Item(text=token.pos,
                                  id='{}pos'.format(token_id),
                                  alignment=token_id)
            tier.append(token_pos_item)


    num_subwords = 0
    # -- 2) Iterate through the words.
    for word_i, word in enumerate(phrase): # type: int, Word
        if word_dict:
            word_id = word.id if word.id else '{}{}'.format(word_dict[ID_KEY], word_i + 1) # The ID for this word token
            word_item = Item(text=word.hyphenated, id=word_id)
            word_tier.append(word_item)

            # Only add POS tags if present.
            add_to_pos_tier(word, word_id, word_pos_tier)

        # -- 3) Iterate through subwords.
        if sw_dict:
            for subword in word:
                subword_id = subword.id if subword.id else '{}{}'.format(sw_dict[ID_KEY],
                                                                         num_subwords+1)

                subword_item = Item(text=subword.string, id=subword_id)

                if subword.alignments and sw_dict.get(ALN_KEY):
                    subword_item.alignment = ','.join([sw.id for sw in subword.alignments if sw.id])
                    subword_tier.alignment = sw_dict[ALN_KEY]

                if word_dict:
                    subword_item.segmentation=word_id
                subword_tier.append(subword_item)

                add_to_pos_tier(subword, subword_id, subword_pos_tier)
                num_subwords += 1  # Make sure to increment the index

    # Add our tiers to the parent Igt instance
    if word_dict:
        igt.append(word_tier)
        if word_pos_tier:
            igt.append(word_pos_tier)

    if sw_dict:
        igt.append(subword_tier)
        if subword_pos_tier:
            igt.append(subword_pos_tier)

def xigt_add_bilingual_alignment(xigt_inst: Igt, trans: Phrase):
    """
    Given the translation phrase object, add the encoded alignments
    to a bilingual-alignments tier.
    """

    bilingual_aln_tier = Tier(id='a', type='bilingual-alignments',
                              attributes={'source':'tw', 'target':'g'})
    aln_num = 0
    for t_w in trans:
        for aligned_gloss in t_w.alignments:


            aln_item = Item(id='a{}'.format(aln_num+1),
                            attributes={'source':t_w.id,
                                        'target':aligned_gloss.id})
            bilingual_aln_tier.append(aln_item)
            aln_num += 1
    xigt_inst.append(bilingual_aln_tier)

def xigt_add_dependencies(xigt_inst: Igt, phrase: Phrase):
    """
    Given a phrase that has a dependency structure analysis,
    render it into
    """
    dep_tier = Tier(type='dependencies', id='{}ds'.format(phrase.id))
    for i, dep_link in enumerate(phrase.dependencies):
        dep_item = Item(id='{}-dep{}'.format(phrase.id, i+1),
                        attributes={'dep':dep_link.child.id})
        if dep_link.parent:
            dep_item.attributes['head'] = dep_link.parent.id
        if dep_link.type:
            dep_item.text = dep_link.type
        dep_tier.append(dep_item)
    xigt_inst.append(dep_tier)


def instance_to_xigt(inst: Instance):
    """
    Take an INTENT2 representation and convert it to Xigt.

    :rtype:  Igt
    """
    xigt_inst = Igt(id=inst.id)
    tier_to_xigt(xigt_inst, inst.lang, LANG_KEY)
    tier_to_xigt(xigt_inst, inst.gloss, GLOSS_KEY)
    tier_to_xigt(xigt_inst, inst.trans, TRANS_KEY)
    xigt_add_bilingual_alignment(xigt_inst, inst.trans)
    xigt_add_dependencies(xigt_inst, inst.trans)
    return xigt_inst

