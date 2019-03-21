from unittest import TestCase

from intent2.alignment import heuristic_alignment, gloss_to_morph_align
from intent2.model import Instance, DependencyLink, DependencyStructure
from intent2.projection import project_ds


class DSCycleTests(TestCase):
    def test_cycle(self):
        bul_strs = ['Procetox        statija-ta=i',
                    'read.1sg      article-DEF=3fsg',
                    'I read her article.']
        inst = Instance.from_strings(bul_strs)

        heuristic_alignment(inst)
        gloss_to_morph_align(inst)
        project_ds(inst)

        # Create the target DS
        d1 = DependencyLink(inst.lang[0], parent=None, link_type='root')
        d2 = DependencyLink(inst.lang[1], inst.lang[0], link_type='dobj')
        tgt_ds = DependencyStructure({d1, d2})

        self.assertEqual(tgt_ds, inst.lang.dependency_structure)
