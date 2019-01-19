#Heuristic Alignment

One of INTENT's main enrichment functions is to align translation and language lines in an IGT instance via the use of the gloss line.

## Overview

The system runs as a "sieve" function, starting with the highest-precision heuristics to find alignments and gradually introducing lower-precision, higher-recall elements.

### 1. Heuristics

#### a) Exact Match — Language+Translation

The first heuristic pass checks the language line and translation lines for exact matches, to 

#### b) Exact Match — Gloss+Translation

The next heuristic pass checks for whether the gloss and translation lines posess any exact string matches.

#### c) Lemma Match

Next, check whether there are words between the gloss line and translation line that share common roots.

#### d) Substring Match

Similar to lemma, but a little looser, check to see if there are any elements on the gloss line that contain exact substring matches of words in the translation line and vice versa (with a minimum of **three characters**).

### 2. Multiple Alignments

![Illustration of multiple alignments.](/Users/rgeorgi/Documents/code/intent2/doc/images/aln1.png)

In the case where there are multiple alignments between potential gloss tokens and translation tokens, the behavior is as follows:

![](/Users/rgeorgi/Documents/code/intent2/doc/images/aln2.png)

Candidate tokens are aligned left to right monotonically, with any remaining tokens assigned to the last aligned token. 

## Morphemes vs. Words

The process of POS projection is done initially between words and morphemes