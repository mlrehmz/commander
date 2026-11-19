# HelpCat: Evidence-Based Extraction of CLI Help

## 1. Goal and completion criteria

Build a CPU-trained help parser and a reproducible experiment answering:

> Can learned line classification improve flag extraction over deterministic rules while maintaining high precision, useful coverage, and auditable evidence?

The primary deliverable is the experiment. The usable artifact is a Python library and CLI that parse supplied help text into validated JSON.

**Initial scope**

- English, conventional CLI help supplied as text or captured files.
- One captured invocation per example, with an explicitly supplied command path.
- Extract flags, advertised subcommands, positionals, descriptions, and supported semantic fields.
- Preserve evidence for extracted values and abstain when interpretation is unsupported.
- Compare deterministic rules, a CRF, and one compact neural model.

**Deferred work**

Live execution of installed binaries, recursive command discovery, large-scale package harvesting, daemons, HTTP/MCP interfaces, quantization, additional neural architectures, and active learning.

Completion does not require the neural model to win. A reproducible negative result with documented limitations satisfies the research goal.

## 2. Public interface and extraction contract

### Library and CLI

Expose one primary library interface:

```python
parse_help(
    text: str,
    *,
    command_path: tuple[str, ...],
    engine: ParserEngine,
) -> Catalog
```

`ParserEngine` owns the selected tagger, calibration policy, and versioned configuration. Load it once for repeated library calls.

Provide these CLI operations:

```text
helpcat parse help.txt --command tar
helpcat parse - --command git --command commit
helpcat query catalog.json --flag=-x
```

- `parse` reads a file or stdin; it never executes a command.
- JSON goes to stdout; diagnostics go to stderr.
- Exit codes: `0` for `ok` or `partial`, `1` for extraction failure, `2` for invalid arguments or unreadable input.
- `query` reads an existing catalog. Return an explicit not-found or ambiguous result instead of guessing.
- Ship the selected engine and its calibration policy together. Support explicit engine selection for research comparisons.

### Canonical source and evidence

- Accept UTF-8 text; remove a leading BOM, normalize CRLF/CR to LF, and strip recognized ANSI sequences.
- Preserve raw input hashes and the exact canonical text against which spans are defined.
- Preserve tabs in canonical text; expand them only when calculating layout features.
- Use one-based line numbers and zero-based, half-open Unicode character columns.
- Permit multiple spans for wrapped descriptions and other discontinuous evidence.
- Every source-derived string carries evidence. Normalized values reference their evidence and transformation rule.
- Reject inputs exceeding 1 MiB, 10,000 lines, or 4,096 characters per line. Never silently truncate.
- Invalid encoding, unsupported terminal controls, and limit violations produce explicit failure diagnostics.

### Catalog schema

Use JSON Schema draft 2020-12 with a versioned schema identifier.

Represent:

- Invocation command path and capture metadata.
- Flags with aliases, metavar, argument arity, required presence, type, default, choices, description, evidence, and provenance.
- Advertised subcommands and positionals.
- Extraction status, abstention reasons, and selection scores.

Apply these rules:

- Distinguish unknown values from explicit absence.
- Separate value arity (`none`, `required`, `optional`, `unknown`) from whether an option must appear.
- Treat `takes_value` as a derived convenience field; preserve unknown arity.
- Record source literals separately from normalized interpretations.
- Use provenance values for direct extraction and deterministic inference.
- Infer semantic fields only through documented, tested rules. Otherwise leave them unknown.
- Never infer subcommand hierarchy beyond the supplied invocation and advertised entries.
- Merge aliases only when the source explicitly groups them. Keep identical spellings in different command scopes distinct.
- Preserve expanded forms such as `--[no-]color` through a named normalization rule and evidence for the original notation.

Define statuses precisely:

- `ok`: recognizable help was parsed without detected extraction omissions or conflicts.
- `partial`: usable records remain, but ambiguous candidates, unsupported sections, or conflicts caused omissions.
- `failed`: no reliable interpretation is available or the input violates the input contract.

Unknown optional semantic fields alone do not make a result `partial`. `ok` does not claim perfect recall.

## 3. Research corpus and reference annotations

### Prior art and collection pilot

Before implementing framework-specific extraction:

1. Verify the existence, behavior, maintenance, and licensing of the proposed prior-art projects.
2. Examine relevant help parsers, completion generators, man-page extraction tools, and the original CRF work.
3. Maintain a research log containing the source URL, claim, verification evidence, and relevance.
4. Write a short related-work document distinguishing established techniques from this project’s contribution.

Survey up to 100 projects. Record formatter family, version, help availability, man pages, completion files, machine-readable specification surfaces, and redistribution permissions.

Prefer committed help snapshots and reproducible formatter-generated fixtures. When execution is necessary, use a dedicated collection container with no network during execution, read-only root, temporary writable storage, a throwaway home, and explicit timeout, output, memory, CPU, and PID limits. Never execute harvested commands on the host.

**Framework-adapter gate:** implement at most one initial adapter, and only if its family represents at least 15% of the survey and a pilot on ten examples improves flag recall by at least five percentage points at the precision target. Use training/development examples for this decision.

### Corpus and splits

Target 100 distinct projects, with no more than three captured invocations per project.

- Reserve 20 Cobra projects and 20 clap projects for unseen-family evaluation.
- Split the remaining 60 projects into 36 training, 12 development, and 12 familiar-family test projects.
- Cover argparse, Click, Go `flag`, GNU-style help, and irregular layouts in the remaining projects.
- Group forks, copied templates, near-duplicate pages, and synthetic-spec descendants before splitting.
- Assign ambiguous formatter families to `unknown`; do not use uncertain assignments as evidence of family transfer.
- If leakage grouping prevents the target counts, collect replacement projects before freezing the manifest.

Separate input files, metadata, annotation records, and split manifests. Treat captures and adjudicated annotations as authoritative; features, predictions, and caches are derived.

Record tool version, invocation, locale, terminal width where known, source URL, license evidence, capture hashes, and normalization version. Redistribute only material with documented permission; otherwise provide retrieval instructions and hashes.

### Annotation protocol

Pilot ten difficult pages before scaling. Define ten line labels:

```text
usage
section_heading
option_declaration
option_continuation
description_continuation
subcommand_declaration
positional_declaration
prose
blank
other
```

Use declaration labels for mixed declaration/description lines; the assembler handles their internal structure.

Annotate both line labels and complete reference records, including alias grouping, command scope, evidence, and semantic uncertainty.

- Double-annotate at least 20% of projects using a separate blind pass; adjudicate disagreements against the source.
- Record annotator identity and whether annotations were human- or agent-produced.
- Describe agent-produced references honestly; do not call them human gold.
- Audit the final reference set independently of model predictions.
- Keep silver annotations from man pages, completions, or source specifications out of final evaluation.
- Validate synthetic rendering alignment before treating generated span labels as exact.
- Confine synthetic examples and their descendants to training data.

Freeze and hash the test manifests after annotation adjudication. Routine development commands must exclude test data.

## 4. Implementation sequence and gates

### A. Establish the project and preregistration

Use Python, `uv`, pinned dependencies, a lockfile, pytest, schema validation, and a Makefile. Verify dependency compatibility and licenses before pinning.

Keep runtime dependencies separate from research/training dependencies. Load neural dependencies only when the selected engine needs them.

Record architecture decisions and update the existing progress log with completed work, evidence, remaining steps, and blockers.

Before model evaluation, commit a preregistration containing:

- Dataset and split definitions.
- Correctness and matching rules.
- Precision target and model-selection rule.
- Training configurations, seeds, and compute budgets.
- Performance benchmark procedure.
- Planned analyses and stopping rules.

### B. Implement normalization and the deterministic assembler

Build the assembler before substantial model training.

Its input is canonical text plus line labels and selection scores. Its output is a schema-valid catalog with evidence and diagnostics.

Support at least:

```text
-v, --verbose
--color[=WHEN]
--[no-]foo
-I<dir>
```

Handle wrapped declarations, wrapped descriptions, repeated global options, multiple option sections, tabs, Unicode, and prose containing flag-like strings.

Use layout candidates and a tokenizer rather than assuming the first two-space gap always marks a description boundary.

**Assembler gate:** feed reference line labels into the assembler. Require at least 99% flag precision and 90% flag recall on development data, plus valid evidence for every emitted source-derived field. If the gate fails, fix the assembler or document and narrow the unsupported scope before training.

### C. Build the baselines

Implement:

1. A deterministic layout and tokenization baseline.
2. A line CRF using geometry, lexical, and neighboring-line features.
3. Any framework adapter approved by the survey gate.

All internal taggers use the same assembler and semantic rules. Report complete external parsers separately because they do not share that extraction pipeline.

### D. Train one neural model

Use a character CNN over the first 48 UTF-8 bytes of each line, combined with layout and lexical features, followed by a two-layer bidirectional GRU with hidden size 128 per direction and a linear classification head.

Keep full canonical lines available to the assembler; feature truncation must not truncate evidence.

- Run on CPU with a fixed, recorded thread count.
- Split long pages into overlapping windows of 256 lines with 32-line overlap; retain predictions from the window offering the most context.
- Use AdamW, initial learning rate `1e-3`, gradient clipping at `1.0`, and page-window batch size `8`.
- Cache versioned features keyed by content hash and feature configuration.
- Select checkpoints using development data only.
- Save resumable checkpoints atomically, including optimizer state, seed, configuration, and code revision.

**Overfit gate:** on eight training pages, require at least 99.5% training line accuracy before the main experiment. Investigate optimization, label alignment, and windowing if it fails.

Run three fixed seeds for the neural model, with the same preregistered CPU budget per seed. Use a 90-minute budget per seed and checkpoint every ten minutes.

Limit initial neural ablations to:

- Geometry and lexical features without the character CNN.
- Real-only versus mixed real/synthetic training.

Defer transformer, TCN, CRF-head, and quantization experiments.

### E. Calibrate abstention and select the release engine

Learn or calibrate record-selection scores against end-to-end development correctness. Raw line probabilities are not catalog confidence.

For each engine, choose the threshold maximizing macro-average per-tool recall subject to:

- Development flag precision of at least **99%**.
- At least **500 accepted flag records** across the development corpus.

If no threshold qualifies, report that outcome. Do not lower the target after seeing results.

Prefer the simplest qualifying engine. Promote the neural model over the strongest simpler engine only if development recall improves by at least **three absolute percentage points** and it meets the resource limits.

If no engine qualifies, ship the rules engine as an explicitly experimental parser and report that the precision objective was not demonstrated.

Freeze the selected engine, threshold, schema, matching rules, and evaluation procedure before opening either test track.

## 5. Evaluation, verification, and delivery

### Final evaluation

Evaluate the frozen pipeline once on:

1. Unseen projects using familiar formatter families.
2. Entirely held-out Cobra and clap families.

Report:

- Line-label macro-F1.
- Flag precision and recall, both pooled and macro-averaged per project.
- Alias grouping and command-scope correctness.
- Per-field accuracy and support for arity, descriptions, defaults, choices, types, and required presence.
- Unsupported additions separately from incorrect interpretations.
- Record selection rate, page success rate, and partial/failure frequency.
- Risk–coverage curves with explicitly defined denominators.
- Per-family results and variability across training seeds.
- Cold-start and warm latency, peak memory, and artifact size.

Use exact flag spelling plus supplied command scope for identity matching; score alias grouping separately. Normalize description whitespace for description comparison, while testing evidence spans exactly.

Generate 95% confidence intervals using 2,000 bootstrap resamples clustered by project. Report sample sizes and sparse-error limitations; an observed 99% precision does not establish a guaranteed error bound.

Benchmark on a recorded CPU environment with fixed thread settings and a fixed development workload. The release-engine limits are warm p95 latency of 500 ms for pages up to 200 lines, peak RSS of 512 MiB, and model artifacts of 50 MiB. Report longer-page and cold-start costs separately.

Classify up to 100 sampled errors—or all errors if fewer—including false flags, missed declarations, alias mistakes, description attachment, tokenization, scope, and semantic inference.

Any changes made after viewing test results belong to a separately labeled exploratory revision.

### Required tests

Use focused behavior tests first, followed by integration and property tests at stable interfaces.

Cover:

- Normalization, Unicode, tabs, ANSI sequences, malformed input, and size limits.
- Span bounds, substring fidelity, discontinuous evidence, and normalization provenance.
- Flag notation variants, ambiguous value arity, wrapped text, repeated options, and command scopes.
- Abstention, empty results, unsupported help, and partial extraction.
- Schema validity, unique record identity, and deterministic output.
- CLI/library agreement, exit codes, query ambiguity, and clean stdout.
- Split leakage, synthetic alignment, cache invalidation, and checkpoint recovery.
- Real tagger-to-assembler handoffs and end-to-end regression fixtures.

Use Hypothesis for span, normalization, duplication, and schema invariants.

### Reproducibility and final artifacts

Provide:

- Installable CLI and library with the selected engine and calibration configuration.
- Versioned schema, annotation guidelines, corpus manifests, and permitted fixtures.
- Research log, related work, architecture decisions, dataset datasheet, and model card.
- A comparison report containing confidence intervals, error examples, negative results, and limitations.
- A README showing installation, file-based parsing, querying, and reproduction.
- One command for development checks and one explicit command for final evaluation.
- Lockfile, seeds, dataset hashes, configurations, and code revisions sufficient to reproduce reported results.

The project is complete when these artifacts reproduce the comparison and accurately describe where extraction succeeds, abstains, or fails. Broader collection or product features require a separate plan.
