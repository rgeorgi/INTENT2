"""
A series of helpful tools to visualize different
aspects for printing and debugging.
"""

from intent2.model import Instance, Word, SubWord, Phrase, TransWord
from typing import Union
from termcolor import colored
import graphviz
from matplotlib import pyplot

def find_lengths(*iters):
    """

    """
    col_widths = []
    for i in range(max([len(iter) for iter in iters])):
        for iter in iters:
            iter_width = 0 if i >= len(iter) else iter[i]
            if i >= len(col_widths):
                col_widths.append(iter_width)
            else:
                col_widths[i] = max(col_widths[i], iter_width)
    return col_widths


def format_token(width, token, aln_type='<', color=None):
    token =  '{{:{}{}}}'.format(aln_type, width+1).format(token)
    if color is not None:
        token = colored(token, color)
    return token

def visualize_alignment(inst: Instance):
    """
    Function to take an instance, and print it out in an easy-to-read
    way with alignments
    """

    # To make sure we align the columns of text, keep track of the max
    # lengths of each token in lang/gloss
    ret_str = ''
    lang_widths = [len(lw.hyphenated) for lw in inst.lang]
    gloss_widths = [len(gw.hyphenated) for gw in inst.gloss]
    alignments = [sorted([aligned_obj.index for aligned_obj in gloss_w.alignments if isinstance(aligned_obj, TransWord)]) for gloss_w in inst.gloss]
    aln_strings = ['({})'.format(','.join([str(i) for i in aln_iter])) if aln_iter else '' for aln_iter in alignments]
    aln_widths = [len(aln) for aln in aln_strings]

    col_widths = find_lengths(lang_widths, gloss_widths, aln_widths)

    for i in range(len(col_widths)):
        ret_str += format_token(col_widths[i], '[{}]'.format(i), aln_type='<', color='blue')
    ret_str += '\n'

    for i, lang_w in enumerate(inst.lang):
        ret_str += format_token(col_widths[i], lang_w.hyphenated)
    ret_str += '\n'

    for j, gloss_w in enumerate(inst.gloss):
        ret_str += format_token(col_widths[j], gloss_w.hyphenated)
    ret_str += '\n'

    # Now, print alignments
    for i, aln_tup in enumerate(aln_strings):
        ret_str += format_token(col_widths[i], aln_tup, aln_type='^', color='green')
    ret_str += '\n'

    trans_word_widths = [len(trans_w.hyphenated) for trans_w in inst.trans]
    trans_labels = ['({})'.format(i) for i in range(len(inst.trans))]
    trans_label_widths = [len(tl) for tl in trans_labels]
    trans_word_widths = find_lengths(trans_word_widths, trans_label_widths)

    for i, trans_w in enumerate(inst.trans):
        ret_str += format_token(trans_word_widths[i], trans_w.hyphenated)
    ret_str += '\n'

    for i, label in enumerate(trans_labels):
        ret_str += format_token(trans_word_widths[i], label, aln_type='<', color='green')
    ret_str += '\n'

    print(ret_str)
    return ret_str

def draw_alignment(inst: Instance):
    """
    Represent the instance with a png graph
    """
    dot = graphviz.Graph(engine='fdp')

    def phrase_to_subgraph(p: Phrase, v_level):
        with dot.subgraph(name=p.id) as sg:
            for i, word in enumerate(p):
                sg.node(word.id,
                        label=word.hyphenated,
                        shape='plaintext',
                        pos='{0},{1}!'.format(i, v_level))

    # Attempt to space the vertical distance between trans/gloss
    # proportional to the length of the gloss tier, otherwise
    # it is hard to read.
    height_sep = max(1, len(inst.gloss) / 10)

    phrase_to_subgraph(inst.lang, height_sep + 1)
    phrase_to_subgraph(inst.gloss, height_sep * 1)
    phrase_to_subgraph(inst.trans, 0)

    for tw, gw in inst.trans.aligned_words(): # type: Word, Word
        dot.edge(tw.id, gw.id)

    for lw, gw in inst.lang.aligned_words(): # type: Word, Word
        dot.edge(lw.id, gw.id)


    dot.attr(overlap='false', sep='1')
    png = dot.pipe(format='png')
    return png

def alignment_to_png(inst: Instance, path: str):
    """
    Save the visualized alignment to a png.
    """
    with open(path, 'wb') as png_f:
        png_f.write(draw_alignment(inst))

