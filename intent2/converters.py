"""
Module to do conversions between different formats.
"""
import sys
import unittest

import xigt.codecs.xigtxml
from xigt.model import Igt
import xigt.query
from intent2.xigt_helpers import xigt_find
from intent2.model import SubWord, Word, Phrase
import re

def create_lang_phrase(inst) -> Phrase:
    """
    :type inst: Igt
    :return:
    """
    # Start with morphemes.
    morphs = xigt_find(inst, id='m')

    p = Phrase()
    cur_sws = []
    last_word = None

    def add_word():
        nonlocal cur_sws
        p.add_word(Word(subwords=cur_sws))
        cur_sws = []

    for morph in morphs:
        if last_word is not None and morph.segmentation != last_word:
            add_word()
        sw = SubWord(morph.text)
        cur_sws.append(sw)
        last_word = morph.segmentation

    add_word()
    return p

def create_gloss_phrase(inst) -> Phrase:
    glosses = xigt_find(inst, id='g')

    p = Phrase()
    cur_glosses = []
    last_word = None

    def add_word():
        nonlocal cur_glosses
        p.add_word(Word(subwords=cur_glosses))
        cur_glosses = []

    for gloss in glosses:
        aligned_morph = xigt_find(inst, id=gloss.alignment)
        aligned_word = aligned_morph.segmentation
        if last_word is not None and aligned_word != last_word:
            add_word()
        sw = SubWord(gloss.text)
        cur_glosses.append(sw)
        last_word = aligned_word
    add_word()
    return p



def read_xigt(xigt_path):
    """
    Convert Xigt to INTENT internal structure.
    :param xigt_path:
    :return:
    """
    with open(xigt_path, 'r', encoding='utf-8') as xigt_f:
        corp = xigt.codecs.xigtxml.load(xigt_f)
        inst = corp[0]

        # Create the representation of the
        # language morphemes and words.
        l = create_lang_phrase(inst)

        # Next, the phrase representation of the translation
        translation = xigt_find(inst, id='t')[0].value()
        t = Phrase([Word(s) for s in translation.split()])

        # Finally, create the glosses.
        # Assume that they have alignment to
        g = create_gloss_phrase(inst)

        print(l)
        print(g)
        print(t)

        for gw, lw in zip(g, l):
            gw.add_alignment(lw)
            print(gw.alignments)


def process_toolbox_instance(toolbox_instance):
    """
    Instances from toolbox files look like the following:

        \ref 20030701TifolafengBapakAnde1_0003
        \ELANBegin 9.371
        \ELANEnd 15.509
        \ELANParticipant Andirias Padafani
        \sound 20030701TifolafengBapakAnde1.wav 9.371 15.509
        \t heelo              maiye, ni           ni'aduo             hamintaahi,#    ni           yaa pun   namei.#
        \m he-    nil   -o    maiye  ni           ni-          adua   ha-    mintaahi ni           yaa pun   namei
        \g 3.LOC- do.so -PNCT if     1PL.EXCL.AGT 1PL.EXCL.AL- master 3.PAT- pray.CPL 1PL.EXCL.AGT go  field prepare.field
        \p pro-   v.loc -asp  conj   pro          pro-         n      pro-   v.pat    pro          v.0 n     v.0

        \f when it is that time, we pray to the Lord and go work in the fields

    Given this format, attempt to parse into INTENT objects.

    :type toolbox_instance: str
    :return:
    """

    # -- 1a) Define a method to retrieve lines from the instance preceded by the given linetype
    #        (Noting that there can be multiple entries for the same linetype per instance)
    def get_toolbox_line(linetype: str) -> str:
        line_matches = re.findall('\\\\{}\s+(.*)\n'.format(linetype), toolbox_instance)
        return None if not line_matches else ' '.join(line_matches)

    # -- 1b) Get all the types of lines from the instance, if they exist.
    trans_string = get_toolbox_line('f')
    gloss_string = get_toolbox_line('g')
    morph_string = get_toolbox_line('m')
    lang_string = get_toolbox_line('t')

    # -- 1c) Abort if we do not have all four lines.
    if not (trans_string and gloss_string and morph_string and lang_string):
        return None

    # -------------------------------------------
    # Parse.
    # -------------------------------------------
    lang_p = Phrase()

    columnar_re = re.compile('\S+\s*(?=\S|$)')

    morph_line_concatenated = re.sub('\s*-\s*', '-', morph_string)

    # -------------------------------------------
    # Methods to combine information
    # -------------------------------------------






def read_toolbox(toolbox_path):
    with open(toolbox_path, 'r', encoding='utf-8', errors='replace') as f:
        instances = re.findall('\\\\ref[\s\S]+?(?=\\\\ref|$)', f.read())
        for instance in instances:
            process_toolbox_instance(instance)




if __name__ == '__main__':
    read_xigt('/Users/rgeorgi/Documents/code/intent/data/testcases/khowell/abz_1igt_raw_tier.xml')
    # read_toolbox('/Users/rgeorgi/Documents/code/intent2/intent2/data/toolbox/AbuiCorpus.txt')