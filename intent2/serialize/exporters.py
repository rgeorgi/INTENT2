from intent2.model import Instance, Corpus, Phrase, IdMixin, Word, SubWord, TransWord, TaggableMixin
import intent2

from xigt.errors import XigtError
from xigt.model import XigtCorpus, Igt, Tier, Item
from xigt.codecs.xigtxml import dumps
from typing import Iterable, Tuple, Union, List
from datetime import datetime

import logging

from intent2.xigt_helpers import generate_tier_id
from .consts import *

EXPORT_LOG = logging.getLogger('export')

# -------------------------------------------
# CONSTANTS
# -------------------------------------------
INTENT2_DATA_PROV = 'INTENT2-{}'.format(intent2.__version__)
DATA_PROV_KEY = 'data-provenance'
DATA_METHOD_KEY = 'data-method'
DATA_TIME_KEY = 'data-creation-time'

def add_timestamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# -------------------------------------------

def corpus_to_xigt(corp: Corpus):
    """
    Given an INTENT2 Corpus object,
    return its representation in xigtxml format.
    """
    xc = XigtCorpus()
    EXPORT_LOG.info('Preparing to export INTENT2 Coprus to Xigt')
    for inst in corp:
        xigt_inst = instance_to_xigt(inst)
        try:
            dumps(XigtCorpus(igts=[xigt_inst]))
            xc.append(xigt_inst)
        except (TypeError, XigtError) as te:
            EXPORT_LOG.error('Error in serializing instance "{}": {}'.format(inst.id, te))
    EXPORT_LOG.info('Corpus successfully converted. Returning string for writing.')
    return dumps(xc)


def tier_to_xigt(igt: Igt,
                 phrase: Phrase,
                 phrase_type: str):
    """
    Given
    """
    # -- 0) Do nothing if the phrase is empty.
    if not phrase:
        return

    # -- 1) Create phrase tier if expected, and if
    #       there is a phrase to serialize.
    phrase_dict = get_xigt_str([phrase_type, PHRASE_KEY])
    if phrase and phrase_dict:


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
                         alignment=word_dict.get(ALN_KEY),
                         segmentation=word_dict.get(SEG_KEY))

    # -- 1b) Create the subword tier. (Only add segmentation
    #        if we're also creating a word tier; e.g. lang, not gloss)
    sw_dict = get_xigt_str([phrase_type, SUBWORDS_KEY])
    if sw_dict:
        subword_tier = Tier(type=sw_dict[TYPE_KEY], id=sw_dict[ID_KEY])
        if word_dict:
            subword_tier.segmentation = word_dict[ID_KEY]


    num_subwords = 0
    # -- 2) Iterate through the words.
    for word_i, word in enumerate(phrase): # type: int, Word
        if word_dict:
            word_id = word.id if word.id else '{}{}'.format(word_dict[ID_KEY], word_i + 1) # The ID for this word token
            alignments = [word.id for word in word.aligned_words()]
            word_item = Item(text=word.hyphenated, id=word_id,
                             alignment=','.join(alignments) if alignments else None)
            word_tier.append(word_item)


        # -- 3) Iterate through subwords.
        if sw_dict:
            for subword in word:
                subword_id = subword.id if subword.id else '{}{}'.format(sw_dict[ID_KEY],
                                                                         num_subwords+1)

                subword_item = Item(text=subword.hyphenated, id=subword_id)

                if subword.alignments and sw_dict.get(ALN_KEY):
                    subword_item.alignment = ','.join([a.id for a in subword.alignments
                                                       if a.id
                                                       and isinstance(a, SubWord)])
                    subword_tier.alignment = sw_dict[ALN_KEY]

                if word_dict:
                    subword_item.segmentation = word_id
                subword_tier.append(subword_item)

                num_subwords += 1  # Make sure to increment the index

    # Add our tiers to the parent Igt instance
    if word_dict:
        igt.append(word_tier)

    if sw_dict:
        igt.append(subword_tier)

def xigt_add_pos(xigt_inst: Igt, tokens: List[Union[Word, SubWord]], tgt_id: str, method):
    """
    Given a xigt instance, and list of tagged words or subwords, add
    an appropriate pos-tagged tier to the Xigt instance.
    """
    pos_tier_id = generate_tier_id(xigt_inst, 'pos', tgt_id)
    pos_tier = Tier(type='pos', id=pos_tier_id,
                    alignment=tgt_id,
                    attributes={DATA_PROV_KEY: INTENT2_DATA_PROV,
                                DATA_METHOD_KEY: method,
                                DATA_TIME_KEY: add_timestamp()})
    for i, token in enumerate(tokens):
        if token.pos:
            token_id = '{}_{}'.format(pos_tier_id, i+1)
            pos_item = Item(text=token.pos, id=token_id, alignment=token.id)
            pos_tier.append(pos_item)
    if pos_tier.items:
        xigt_inst.append(pos_tier)
    return pos_tier

def xigt_add_bilingual_alignment(xigt_inst: Igt, trans: Phrase, method):
    """
    Given the translation phrase object, add the encoded alignments
    to a bilingual-alignments tier.
    """

    tw_to_g_tier_id = generate_tier_id(xigt_inst, 'bilingual-alignments', TRANS_WORD_ID, GLOSS_SUBWORD_ID)
    tw_to_g_tier = Tier(id=tw_to_g_tier_id, type='bilingual-alignments',
                        attributes={'source': TRANS_WORD_ID,
                                    'target': GLOSS_SUBWORD_ID,
                                    DATA_PROV_KEY: INTENT2_DATA_PROV,
                                    DATA_METHOD_KEY: method,
                                    DATA_TIME_KEY: add_timestamp()})

    tw_to_lw_id = generate_tier_id(xigt_inst, 'bilingual-alignments', TRANS_WORD_ID, LANG_WORD_ID)
    tw_to_lw_tier = Tier(id=tw_to_lw_id, type='bilingual-alignments',
                         attributes={'source': TRANS_WORD_ID,
                                     'target': LANG_WORD_ID,
                                     DATA_PROV_KEY: INTENT2_DATA_PROV,
                                     DATA_TIME_KEY: add_timestamp()})

    for t_w in trans: # type: TransWord
        for aligned_gloss in [item for item in t_w.alignments if isinstance(item, SubWord)]:


            assert t_w.id is not None
            assert aligned_gloss.id is not None, aligned_gloss

            aln_item = Item(id='{}_{}'.format(tw_to_g_tier_id, len(tw_to_g_tier) + 1),
                            attributes={'source': t_w.id,
                                        'target': aligned_gloss.id})
            tw_to_g_tier.append(aln_item)

        for l_w in t_w.aligned_lang_words:
            tw_lw_item = Item(id='{}_{}'.format(tw_to_lw_id, len(tw_to_lw_tier) + 1),
                              attributes={'source':t_w.id,
                                          'target':l_w.id})
            tw_to_lw_tier.append(tw_lw_item)

    # Only append if it's not empty.
    if tw_to_g_tier:
        xigt_inst.append(tw_to_g_tier)
    if tw_to_lw_tier:
        xigt_inst.append(tw_to_lw_tier)

def xigt_add_dependencies(xigt_inst: Igt, phrase: Phrase, method: str):
    """
    Given a phrase that has a dependency structure analysis,
    render it into
    """
    # Skip adding dependency structure if none exists for this phrase.
    if not phrase.dependency_structure:
        return

    dep_tier_id = generate_tier_id(xigt_inst, 'dependencies', phrase.id)
    dep_tier = Tier(type='dependencies', id=dep_tier_id,
                    attributes={'dep':phrase.id, 'head':phrase.id,
                                DATA_PROV_KEY: INTENT2_DATA_PROV,
                                DATA_METHOD_KEY: method,
                                DATA_TIME_KEY: add_timestamp()})
    for i, dep_link in enumerate(sorted(phrase.dependency_structure,
                                        key=lambda link: link.child.index)):
        dep_item = Item(id='{}_dep{}'.format(dep_tier_id, i+1),
                        attributes={'dep':dep_link.child.id})
        if dep_link.parent:
            dep_item.attributes['head'] = dep_link.parent.id
        if dep_link.type:
            dep_item.text = dep_link.type
        dep_tier.append(dep_item)
    if dep_tier:
        xigt_inst.append(dep_tier)


def xigt_add_all_pos(inst: Instance, xigt_inst: Igt, method):
    xigt_add_pos(xigt_inst, inst.lang, LANG_WORD_ID, method)
    xigt_add_pos(xigt_inst, inst.gloss, GLOSS_WORD_ID, method)
    xigt_add_pos(xigt_inst, inst.gloss.subwords, GLOSS_SUBWORD_ID, method)
    xigt_add_pos(xigt_inst, inst.trans, TRANS_WORD_ID, method)


def instance_to_xigt(inst: Instance):
    """
    Take an INTENT2 representation and convert it to Xigt.

    :rtype:  Igt
    """
    EXPORT_LOG.debug('Serializing instance "{}" to Xigt'.format(inst.id))
    xigt_inst = Igt(id=inst.id)
    tier_to_xigt(xigt_inst, inst.lang, LANG_KEY)
    tier_to_xigt(xigt_inst, inst.gloss, GLOSS_KEY)
    tier_to_xigt(xigt_inst, inst.trans, TRANS_KEY)

    return xigt_inst


