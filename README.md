# INTENT2

INTENT2 is a rewrite of the [INterlinear Text ENrichment Toolkit](https://github.com/rgeorgi/INTENT2.git), updating the codebase to be cleaner, and pure python whenever possible.

INTENT2 ingests [Xigt](https://github.com/xigt/xigt)-formatted Interlinear Glossed Text, and performs:

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

**N.B.** Currently, the code is in an alpha stage. Not all of the functionality is implemented, and what is may contain bugs.

## Running Enrichment

In order to enrich a compatible [Xigt](https://github.com/xigt/xigt)-XML document, you may install

## Input Requirements

INTENT2 requires a [Xigt](https://github.com/xigt/xigt) input file that contains instances with:

- **Language Line** of `type="words"`
- For morpheme-level analysis, either:
  - a `segmentation=w` tier pre-segmented, or
  - Usage of hyphens for morpheme boundaries `-` and equals `=` for clitics within the words of the language line.
- **Gloss Line** of `type="glosses"`
- **Translation Line** of `type=translations` 