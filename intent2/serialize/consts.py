"""
This module holds the definitions and logic
for the xigt-related conventions.

If we wish to generate how instances are identified,
or what tiers have words/phrase tiers, etc, the
"xigt_conventions" var should be modified.
"""

from typing import List

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
                    GLOSS_KEY:{WORDS_KEY: {TYPE_KEY:'glosses', ID_KEY:'gw'},
                                SUBWORDS_KEY: {TYPE_KEY:'glosses', ID_KEY:'g', ALN_KEY:'m', SEG_KEY:'gw'}},
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

LANG_WORD_ID = get_xigt_str([LANG_KEY, WORDS_KEY, ID_KEY])
TRANS_WORD_ID = get_xigt_str([TRANS_KEY, WORDS_KEY, ID_KEY])

GLOSS_SUBWORD_ID = get_xigt_str([GLOSS_KEY, SUBWORDS_KEY, ID_KEY])