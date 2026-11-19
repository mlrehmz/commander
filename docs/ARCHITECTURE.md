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
