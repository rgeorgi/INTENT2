"""
Use this for evaluating different aspects of intent
"""
from collections import defaultdict
from typing import Set, Tuple

from sklearn.metrics import confusion_matrix, classification_report

import numpy as np

from intent2.model import AlignableMixin, Instance, SubWord, Word, TransWord


class PRFEval(object):
    def __init__(self):
        self.matches = 0
        self.system_counts = 0
        self.gold_counts = 0
        self.compares = 0
        self.instances = 0
        self.true = []
        self.pred = []

        self.labels = set([])

    @property
    def precision(self):
        if self.system_counts == 0:
            return 0
        else:
            return self.matches / self.system_counts

    def add_pair(self, gold, pred):

        if gold is not None:

            self.true.append(gold)
            self.pred.append(pred if pred else 'NONE')

            self.labels.add(gold)
            self.compares += 1
            if pred:
                self.system_counts += 1
            if gold == pred:
                self.matches += 1
            self.gold_counts += 1

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

    def confusion_matrix(self):
        return confusion_matrix(self.true, self.pred)


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
        aln_hyp = inst.trans.aligned_words()
    else:
        aln_hyp = {(src, tgt) for src, tgt in inst.trans.alignments if isinstance(tgt, SubWord)}

    count_dict.matches += len(aln_gold & aln_hyp)
    count_dict.system_counts += len(aln_hyp)
    count_dict.gold_counts += len(aln_gold)
    count_dict.instances += 1


def eval_pos(gold_tags, tgt_tags,
             eval: PRFEval):
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

    for gold_tag, tgt_tag in zip(gold_tags, tgt_tags):  # type: Word, Word

        # Skip instances where the gold tag is None
        if gold_tag is not None:
            eval.add_pair(gold_tag, tgt_tag)


def eval_pos_report(eval: PRFEval, tier_name: str):
    """
    Print out the evaluation metrics for the POS tagging.
    """
    ret_str = 'POS Evaluation ({}):\n'.format(tier_name)
    ret_str += eval.count_string()
    ret_str += eval.prf_string()

    # ret_str += pretty_print_cm(confusion_matrix(eval.true, eval.pred), labels=sorted(eval.labels))
    labels = sorted(eval.labels)
    ret_str += pretty_print_cm(confusion_matrix(eval.true,
                                                eval.pred, labels=labels),
                               labels)

    ret_str += classification_report(eval.true, eval.pred)
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


def pretty_print_cm(cm, labels, hide_zeroes=False, hide_diagonal=False, hide_threshold=None):
    """
    pretty print for confusion matrixes

    Via https://gist.github.com/zachguo/10296432
    """
    columnwidth = max([len(x) for x in labels] + [5])  # 5 is value length
    empty_cell = " " * columnwidth

    # Begin CHANGES
    fst_empty_cell = (columnwidth - 3) // 2 * " " + "t/p" + (columnwidth - 3) // 2 * " "

    if len(fst_empty_cell) < len(empty_cell):
        fst_empty_cell = " " * (len(empty_cell) - len(fst_empty_cell)) + fst_empty_cell

    # Print header
    ret_str = ''
    ret_str += "    " + fst_empty_cell + " "
    # End CHANGES

    for label in labels:
        ret_str += "{{:{}}} ".format(columnwidth).format(label)

    ret_str += '\n'
    # Print rows
    for i, label1 in enumerate(labels):
        ret_str += "    {{:{}}} ".format(columnwidth).format(label1)
        for j in range(len(labels)):
            cell = "{{:{}d}}".format(columnwidth).format(cm[i,j])
            if hide_zeroes:
                cell = cell if float(cm[i, j]) != 0 else empty_cell
            if hide_diagonal:
                cell = cell if i != j else empty_cell
            if hide_threshold:
                cell = cell if cm[i, j] > hide_threshold else empty_cell
            ret_str += cell + " "

        ret_str += "\n"

    return ret_str