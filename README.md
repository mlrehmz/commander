# HelpCat

Experimental evidence-based parsing of **supplied CLI help**. This implements the parser and
training-pilot stages of [the research protocol](docs/SPEC.md); the full model
comparison remains incomplete. See [comparison status](docs/COMPARISON.md) for remaining gates.

Python 3.12 or 3.13 and uv are required.

```sh
uv sync --locked
uv run helpcat parse help.txt --command tar
cat help.txt | uv run helpcat parse - --command git --command commit
uv run helpcat query catalog.json --flag=-x
```

```python
from helpcat import ParserEngine, parse_help

engine = ParserEngine()  # Load once and reuse.
catalog = parse_help("Options:\n  -v, --verbose  Details\n",
                     command_path=("demo",), engine=engine)
```

JSON goes to stdout; diagnostics go to stderr. Parse exit codes: 0 for ok/partial,
1 for failed extraction, 2 for invalid arguments/unreadable inputs. Query returns
found, not_found, or ambiguous; input catalogs must validate. Command scope is the
supplied invocation; no subcommand hierarchy is invented and no commands run.

Source fields have value, literal, evidence (line/start/end), rule and provenance.
Lines are one-based and columns are half-open zero-based Unicode characters.
Null means unknown. `takes_value` is null when arity is unknown. The schema ships
inside the package. Tabs stay in canonical text. Failed contract inputs have no
canonical interpretation and use an empty canonical text plus a diagnostic.

```sh
make check                         # Tests, properties, style, manifest validation
make pilot-diagnostic              # Training-only regression report; no qualification
make assembler-gate                # Nonzero until actual dev references pass
make final-evaluation              # Guarded: experiment is not yet ready
uv run --group research python -m helpcat.experiment train-crf
```

The last command requires the complete manifest and a passed assembler gate.
For exploratory CRF or neural parsing, use `--engine crf` or `--engine neural` with
`--model PATH --policy POLICY.json`;
the policy must explicitly be experimental (`calibrated: false`) and name engine
`crf` or `neural` as selected. No trained weights are bundled. Runtime rules do not import CRF or neural
libraries. Calibrated release artifacts will need a separate validated loader.

The collection pilot now has ten offline captures and ten independently
annotated, adjudicated and source-audited agent references in training. See [collection workflow](collection/README.md).
The rules parser handles generic bordered layouts, compound metavars, wrapped
entries and direct literal defaults/choices ([rules](docs/SEMANTIC_RULES.md)).
The CPU neural implementation, cache and checkpoint recovery are smoke tested;
substantial training and final evaluation remain gated on the full corpus.

See [architecture](docs/ARCHITECTURE.md), [preregistration](docs/PREREGISTRATION.md),
[annotation protocol](docs/ANNOTATION_GUIDELINES.md), [datasheet](docs/DATASHEET.md),
and [model card](docs/MODEL_CARD.md). The original prototype was archived before
this project was initialized; its location is recorded in PROGRESS.md.

Expansion checkpoint: [100 source candidates, 56 capture-contract-valid outputs, and 40 locked held-out assets](collection/expansion/README.md). Only the ten audited pilot references are admitted; the full experiment remains incomplete.
