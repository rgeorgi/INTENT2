# INTENT2

INTENT2 is a rewrite of the [INterlinear Text ENrichment Toolkit](https://github.com/rgeorgi/INTENT2.git), the result of my doctoral dissertation research [[pdf](https://digital.lib.washington.edu/researchworks/bitstream/handle/1773/37168/Georgi_washington_0250E_16542.pdf?sequence=1&isAllowed=y)].

The main goals of this rewrite are to increase the ease of distribution, allowing for a simple download and `pip install` using pure python, whenever possible.

#### What does it Do?

INTENT2 ingests [Xigt](https://github.com/xigt/xigt)-formatted Interlinear Glossed Text (IGT), and performs:

- Heuristic alignment between translation and gloss lines
- Part-of-speech tagging
  - Via projection from translation line using induced alignments
  - Via classification on gloss words
- Dependency parsing
  - Via projection from translation line using induced alignments

## Installation

INTENT2 requires Python 3.5 or later.

```
pip install -r requirements.txt
pip install .
```

This will install the `intent` script, as well as the following scripts:

*  `merge-xigt`
  * Takes multiple IGT files that may contain markup for the same instances, and merges into a single file, retaining markup from both where possible. 
*  `intent-train-classifier`
  * Train a classifier for identifying part-of-speech tags on the gloss line of instances.
*  `intent-eval-pos`
  * Evaluates the performance of POS tag classification and projection.
  * Requires a file containing existing POS tags for comparison.
*  `intent-filter`
  * Given a `xigt-xml` document, output a new document that contains only instances with the specified features (L,G,T lines, L↔︎G alignment, etc).
*  `intent`
   *  The main enrichment script. 

N.B.** Currently, the code is in an alpha stage. Not all of the functionality is implemented, and what is may contain bugs.

## Running Enrichment

In order to enrich a [Xigt](https://github.com/xigt/xigt)-XML document, you should run the `intent` script after running installation. The usage of the main script is as follows:

    usage: intent [-h] -i INPUT -o OUTPUT [-v] [--no-align] [--no-posproject]
                  [--no-dsproject] [--no-posclass] [-c CLASSIFIER]
                  [--ignore-import-errors] [--ds-thresh DS_THRESH]
                  [--ds-pngs DS_PNGS] [--aln-pngs ALN_PNGS]
    intent: error: the following arguments are required: -i/--input, -o/--output
* The `-i` file specifies the file you wish to enrich, and the `-o` the output file.
* If you wish to use the gloss-POS classification, a model must be specified with `-c` or `--classifier`, 
* The `--ds-pngs` and `--aln-pngs` arguments will specify a directory into which PNG visualizations of the dependency structures and alignments will be generated, one per enriched instance.

### Enrichment Output

INTENT2 will utilize segmentation provided in the input if present, but 

