# HelpCat

**HelpCat turns CLI help text into structured, traceable JSON.** It extracts options and advertised commands while preserving the exact source evidence for every field. It processes only text you supply; it never runs the documented command.

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

## Engineering highlights

- **Evidence-first output:** explicit spans, provenance and extraction rules make results auditable; unknown semantics remain unknown instead of being guessed.
- **One shared interpretation path:** rules and learned taggers feed the same deterministic assembler, schema checks and query interface.
- **Resilient research infrastructure:** corpus admission is hash-bound to annotations and audits; collection uses pinned dependencies and constrained offline containers. Neural feature caching and resumable checkpoints are implemented.
- **A real collection with guarded claims:** 100 help captures are recorded, while only ten source-audited pilot references are currently admitted. See the [comparison report](docs/COMPARISON.md) for what the checks establish and what remains open.

## Research status

This is a working research prototype, not a completed benchmark. The ten-project pilot has independent primary/blind agent annotations, adjudication and source-only audit, and is admitted for training only. Additional annotations, corpus-family and split review, substantial training, calibration and frozen evaluation remain outstanding. The assembler gate and final evaluation therefore remain closed; no model performance or precision claim is made. See the [comparison status](docs/COMPARISON.md), [collection notes](collection/README.md), and [progress log](PROGRESS.md) for details.

## Development

```sh
make check
make pilot-diagnostic
make assembler-gate       # Expected to remain closed until development references pass.
make final-evaluation     # Guarded until the preregistered experiment is ready.
```

The experiment tooling is described in the [preregistration](docs/PREREGISTRATION.md), [annotation guidelines](docs/ANNOTATION_GUIDELINES.md), [datasheet](docs/DATASHEET.md) and [model card](docs/MODEL_CARD.md).
