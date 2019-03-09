import re

from intent2.model import GlossWord, LangWord


class TagsetMapping(dict):
    """
    Read in one of the tagset mapping files
    to remap one tagset to another
    """

    @classmethod
    def load(cls, path):
        d = cls()
        with open(path, 'r') as f:
            for line in f:
                line_contents = re.search('(^[^#]+)', line)
                if line.strip() and line_contents and line_contents.group(1).strip():
                    fine, course = [elt.strip() for elt in line_contents.group(1).split() if elt.strip()]
                    d[fine] = course
        return d

def get_lg_tag(gw: GlossWord):
    """
    Given a gloss word, retrieve a a "gold"
    tag for this instance. This will likely just
    be the POS tag provided for the gloss tag,
    but if there is one present on the language
    line directly, use that instead.
    """
    lws = list(gw.aligned_words(word_type=LangWord))
    assert len(lws) <= 1
    if lws and lws[0].pos:
        return lws[0].pos
    return gw.pos
