"""
Use this for evaluating different aspects of intent
"""
from collections import defaultdict
from typing import Set, Tuple
from intent2.model import AlignableMixin, Instance, SubWord, Word, TransWord


class PRFEval(object):
    def __init__(self):
        self.matches = 0
        self.system_counts = 0
        self.gold_counts = 0
        self.compares = 0
        self.instances = 0

    @property
    def precision(self):
        if self.system_counts == 0:
            return 0
        else:
            return self.matches / self.system_counts

    @property
    def recall(self):
        if self.gold_counts == 0:
            return 0
        else:
            return self.matches / self.gold_counts

    @property
    def fmeasure(self):
        denominator = (self.precision + self.recall)
        numerator = (self.precision * self.recall)
        if denominator == 0:
            return 0
        else:
            return 2 * numerator / denominator

    def prf_string(self, format_str = '{:>30s} {:.2f}\n'):
        ret_str = ''
        for s, val in [('Precision:', self.precision),
                       ('Recall:', self.recall),
                       ('F-Measure:', self.fmeasure)]:
            ret_str += format_str.format(s, val)
        return ret_str

    def count_string(self, format_str =  '{:>30s} {}\n'):
        ret_str = ''
        for s, val in  [('Instances:', self.instances),
                        ('Sys Counts:', self.system_counts),
                        ('Gold Counts:', self.gold_counts),
                        ('Matches', self.matches)]:
            ret_str += format_str.format(s, val)
        return ret_str

    def __bool__(self):
        return self.instances != 0


def eval_bilingual_alignments(inst: Instance, aln_gold, count_dict: PRFEval):
    """
    Given two sets of alignments,

    :type aln_hyp: Set[Tuple[AlignableMixin,AlignableMixin]]
    :type aln_gold: Set[Tuple[AlignableMixin,AlignableMixin]]
    :return:
    """

    # First, check to see if the gold alignment is supplying
    # Words as alignment objects or Glosses.
    word_alignment = False
    subword_alignment = False
    for gold_src, gold_tgt, in aln_gold:
        if isinstance(gold_tgt, SubWord):
            subword_alignment = True
        if isinstance(gold_tgt, Word):
            word_alignment = True
        assert isinstance(gold_src, TransWord)

    # We want the gold to contain either words to evaluate against
    # or subwords, not both.
    assert not (word_alignment and subword_alignment)

    if word_alignment:
        aln_hyp = inst.trans.aligned_words
    else:
        aln_hyp = {(src, tgt) for src, tgt in inst.trans.alignments if isinstance(tgt, SubWord)}

    count_dict.matches += len(aln_gold & aln_hyp)
    count_dict.system_counts += len(aln_hyp)
    count_dict.gold_counts += len(aln_gold)
    count_dict.instances += 1

def get_lg_tags(inst: Instance):
    """
    Retrieve the gold tags from the instance.

    These will probably be on the gloss phrase, but in case they were
    provided on the lang instance, return those instead.

    :param inst:
    :return:
    """
    lang_tags = inst.lang.tags
    gloss_tags = inst.gloss.tags

    if set(filter(None, lang_tags)):
        return lang_tags
    else:
        return gloss_tags

def eval_pos(gold_tags, tgt_tags,
             eval: PRFEval,
             remap_dict = None):
    """
    Evaluate part of speech tags

    :param gold_tags:
    :param tgt_tags:
    :return:
    """
    assert len(gold_tags) == len(tgt_tags)

    # Skip an instance where no gold tags
    # are provided.
    if not list(filter(None, gold_tags)):
        return
    eval.instances += 1

    remap_dict = {} if remap_dict is None else remap_dict

    for gold_tag, tgt_tag in zip(gold_tags, tgt_tags):  # type: Word, Word

         # If a remap dict is provided, remap the gold tags
        gold_tag = remap_dict.get(gold_tag, gold_tag)

        # Skip instances where the gold tag is None
        if gold_tag is not None:
            if tgt_tag is not None:
                eval.system_counts += 1

            if gold_tag == tgt_tag:
                eval.matches += 1

            eval.gold_counts += 1


def eval_pos_report(eval: PRFEval, tier_name: str):
    """
    Print out the evaluation metrics for the POS tagging.
    """
    ret_str = 'POS Evaluation ({}):\n'.format(tier_name)
    ret_str += eval.count_string()
    ret_str += eval.prf_string()
    return ret_str



def eval_aln_report(eval: PRFEval):
    """

    :param eval:
    :rtype: str
    """
    ret_str = 'Alignment evaluation:\n'
    ret_str += eval.count_string()
    ret_str += eval.prf_string()
    return ret_str