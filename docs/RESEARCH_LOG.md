# Research log — 2026-11-19

This is an initial source check, not the project-family survey. No adapter is approved.

| Source | Claim and verification evidence | Relevance / remaining checks |
|---|---|---|
| [Fish man-page extractor](https://github.com/fish-shell/fish-shell/blob/master/share/tools/create_manpage_completions.py) | Upstream source exists, with Python parser code and a permissive two-condition redistribution notice in this file. | Prior deterministic man-page extraction. Repository license does not substitute for this file's notice. Maintenance cadence and parser quality not audited. |
| [Fish completion authoring](https://github.com/fish-shell/fish-shell/blob/master/doc_src/completions.rst) | Official source describes per-command completion files. | Potential silver metadata, never final reference truth. |
| [help2man in coreutils](https://github.com/coreutils/coreutils/blob/master/man/help2man) | Upstream file exists; GPL notice is visible. The GNU project homepage fetch timed out. | Help-to-man conversion, not equivalent to a validated help-to-catalog parser. Current standalone version and maintenance remain unverified. |
| [CRF original authors' paper](https://home.cs.colorado.edu/~mozer/Teaching/syllabi/6622/papers/LaffertyMcCallumPereira2001.pdf) | Paper text defines sequence labeling with arbitrary observation features. | Established learning method, not this project's invention. Paper redistribution permission not checked; link only. |
| [Lafferty publication list](https://www.cs.cmu.edu/afs/cs/usr/lafferty/www/publications.html) | Author lists the 2001 CRF paper with McCallum and Pereira. | Confirms provenance; institutional repository fetch was forbidden. |
| [python-crfsuite 0.9.12](https://pypi.org/pypi/python-crfsuite/0.9.12/json) | Maintainer metadata lists Python 3.12 support; wrapper MIT, bundled CRFsuite BSD. Local install and real train/predict smoke test pass. | Optional CPU baseline. Full license notices remain upstream. |
| [jsonschema 4.25.1](https://pypi.org/pypi/jsonschema/4.25.1/json) | Maintainer metadata describes draft 2020-12 support and Python 3.12. Local schema validation passes. | Sole runtime dependency; local license metadata recorded in DEPENDENCIES.md. |
| [PyTorch license](https://github.com/pytorch/pytorch/blob/main/LICENSE) | Upstream LICENSE exists; project metadata identifies BSD-3-Clause for the main project. | Candidate neural backend only; not installed or pinned yet. |

No claim is made that all proposed prior art is maintained or suitable. Complete
behavior/license/maintenance verification and the ten-example adapter pilot are
still required before framework-specific extraction. No harvested commands were
executed. Search results are leads; observations above are limited to source text
and local tests, not performance comparisons.
