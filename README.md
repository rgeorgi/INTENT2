# INTENT2

INTENT2 is a rewrite of the [INterlinear Text ENrichment Toolkit](https://github.com/rgeorgi/INTENT2.git), updating the codebase to be cleaner, and pure python whenever possible.

INTENT2 ingests [Xigt](https://github.com/xigt/)-formatted Interlinear Glossed Text, and performs:

- Heuristic alignment between translation and gloss lines
- Part-of-speech tagging
  - Via projection from translation line using induced alignments
  - Via classification on gloss words
- Dependency parsing
  - Via projection from translation line using induced alignments



Currently, the code is in an alpha stage. Not all of the functionality is implemented, and what is may contain bugs.