import re

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
