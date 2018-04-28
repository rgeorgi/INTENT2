import xigt.codecs.xigtxml
import xigt.query
from intent2.xigt_helpers import xigt_find
from intent2.model import SubWord, Word, Phrase

def create_lang_phrase(inst) -> Phrase:
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



if __name__ == '__main__':
    read_xigt('/Users/rgeorgi/Documents/code/intent/data/testcases/khowell/abz_1igt_raw_tier.xml')