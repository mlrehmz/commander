# Architecture and implementation scaffold

The public seams are the supplied `parse_help` API, validated catalogs, and CLI.
A normal input is canonicalized, labeled, assembled, checked, and serialized.
An invalid input yields a failed catalog with diagnostics and no records. An
unreadable CLI input is an argument error. No code executes captured commands.

Canonical text owns all span coordinates. A source field stores a literal,
normalized value, spans, transformation, and provenance. Unknown semantics are
null; arity is a separate enum. ParserEngine owns tagger and selection policy.
All taggers share the assembler. Model imports are lazy. Catalog validation
checks schema and span fidelity at the output boundary.

First behavior check: explicit aliases retain exact evidence. Follow with
normalization failures, wrapped evidence, arity notation, and real CLI roundtrips.
The spec already defines these seams and their acceptance criteria.

Decision: ship only experimental rules until the preregistered calibration gate
passes. Do not provide fake model weights or infer a calibration result from
synthetic unit fixtures. Framework adapters require the separate survey gate.

Remaining authority: captures and adjudicated annotation files, then frozen split
manifests. Features and models are derived and must carry configuration hashes.

## Neural implementation scaffold

The next independent code seam is a CPU line tagger plus versioned feature cache,
window merge and resumable checkpoints. This is implementation/smoke testing only;
substantial training remains behind corpus and assembler gates. Canonical lines
remain full length; only the CNN sees first 48 UTF-8 bytes. Windows have 256 lines
with 32 overlap; choose the prediction with maximal context, with earlier-window
tie breaking. Packed sequences exclude padding from both GRU directions.

The model owns tensors and optimizer state. A training session owns elapsed CPU
budget, RNG state and atomic checkpoints. Cache identity includes canonical hash
and complete feature config. Checkpoints carry seed, model/optimizer/RNG states,
configuration and code revision. A restart must reject mismatched configuration.
Tests cover byte truncation vs intact evidence, window boundaries, cache changes,
actual model inference into the assembler and checkpoint recovery. No test result
will be represented as the eight-page overfit gate or three-seed experiment.
