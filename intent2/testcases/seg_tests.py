from unittest import TestCase
import os

my_dir = os.path.dirname(__file__)
seg_tests_path = os.path.join(my_dir, 'seg_tests.xml')

from xigt.codecs import xigtxml
from xigt import XigtCorpus, Igt

from intent2.xigt_helpers import xigt_find
from intent2.serialize.importers import parse_xigt_instance

# Load the testcase files
with open(seg_tests_path, 'r') as seg_tests_f:
    xc = xigtxml.load(seg_tests_f) # type: XigtCorpus

# -------------------------------------------
# TestCases
# -------------------------------------------
class EsuTest(TestCase):
    def setUp(self):
        self.inst = xigt_find(xc, id='esu-58') # type: Igt

    def test_segmentation(self):
        inst = parse_xigt_instance(self.inst)
        self.assertEqual(len(inst.gloss), 1)

class IkxTest(TestCase):
    def setUp(self):
        self.inst = xigt_find(xc, id='ikx-2') # type: Igt

    def test_diacritics(self):
        inst = parse_xigt_instance(self.inst)
        self.assertEqual(len(inst.lang), 3)
        self.assertEqual(inst.lang[2].string, 'm̀ʉkà')
