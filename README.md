# HelpCat

HelpCat extracts structured options and commands from CLI help text that you provide. It keeps evidence spans so each extracted value can be traced back to the original text. It does not execute the command being documented.

## Try it

Requires Python 3.12 or 3.13 and [uv](https://docs.astral.sh/uv/).

```sh
uv sync --locked
cat <<'DEMO' | uv run helpcat parse - --command demo
Usage: demo [OPTIONS]

Options:
  -v, --verbose  Show progress.
DEMO
```

The CLI prints a JSON catalog to stdout. The verbose flag includes its aliases and source evidence (line 4, the exact character span containing `-v, --verbose`). You can also parse a saved help file or query a catalog:

```sh
uv run helpcat parse help.txt --command tar
uv run helpcat query catalog.json --flag=-x
```

## Python API

```python
from helpcat import ParserEngine, parse_help

engine = ParserEngine()  # Reuse the engine for multiple help pages.
catalog = parse_help(
    "Options:\n  -v, --verbose  Show progress.\n",
    command_path=("demo",),
    engine=engine,
)
```

## What it returns

Catalogs include flags, advertised commands, source metadata and diagnostics. Each extracted field carries its value, literal text, evidence span, extraction rule and provenance. Lines are one-based; columns are zero-based, half-open Unicode character offsets. Unknown values stay null rather than being inferred from descriptions. Query results distinguish `found`, `not_found` and `ambiguous`.

The default rules engine handles common help layouts. Optional CRF and neural engines are experimental; their policies must say `calibrated: false`. No trained model weights are included. See the [semantic rules](docs/SEMANTIC_RULES.md) and [architecture](docs/ARCHITECTURE.md) for details.

## Research status

This is a working research prototype, not a completed benchmark. The repository contains 100 collected help captures; only the ten-project pilot has independently cross-checked, adjudicated and source-audited references, admitted for training only. Additional annotations, corpus-family and split review, substantial training, calibration and frozen evaluation remain outstanding. The assembler gate and final evaluation therefore remain closed. See the [comparison status](docs/COMPARISON.md), [collection notes](collection/README.md), and [progress log](PROGRESS.md) before interpreting results.

## Development

```sh
make check
make pilot-diagnostic
make assembler-gate       # Expected to remain closed until development references pass.
make final-evaluation     # Guarded until the preregistered experiment is ready.
```

The experiment tooling is described in the [preregistration](docs/PREREGISTRATION.md), [annotation guidelines](docs/ANNOTATION_GUIDELINES.md), [datasheet](docs/DATASHEET.md) and [model card](docs/MODEL_CARD.md).
