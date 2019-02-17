"""
Use this for evaluating different aspects of intent
"""
from typing import Set, Tuple
from intent2.model import AlignableMixin, Instance, SubWord, Word, TransWord

def eval_bilingual_alignments(inst: Instance, aln_gold, count_dict):
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

    count_dict['match'] += len(aln_gold & aln_hyp)
    count_dict['hyp'] += len(aln_hyp)
    count_dict['gold'] += len(aln_gold)
    count_dict['instances'] += 1

def print_aln_eval(count_dict):
    precision = count_dict['match'] / count_dict['hyp']
    recall = count_dict['match'] / count_dict['gold']
    fmeasure = 2 * (precision * recall) / (precision + recall)

    print('Alignment evaluation:')
    for s, key in [('Instances:', 'instances'), ('Sys Alignments:', 'hyp'), ('Gold Alignments:', 'gold')]:
        print('{:>30s} {}'.format(s, count_dict[key]))

    for pair in [('Precision:', precision), ('Recall:', recall), ('F-Measure:', fmeasure)]:
        print('{:>30s} {:.2f}'.format(*pair))