# Annotation protocol v1

Use canonical text and Unicode character columns, not expanded tab columns.
Annotate every line, including the empty final line after a trailing newline.
Labels: usage, section_heading, option_declaration, option_continuation,
description_continuation, subcommand_declaration, positional_declaration, prose,
blank, other. Mixed declaration/description lines use declaration labels.

Record complete catalogs with exact evidence, explicit alias groups and supplied
command scope. Unknown fields remain null. Never fill uncertainty from a model.
The reference field must pass validate_catalog. Record canonical_sha256, labels,
reference, annotator, producer (human or agent), adjudicated, blind_pass identity,
and adjudication notes. A blind pass must not see initial labels or predictions.
Pilot ten difficult pages; double-annotate >=20% of projects; audit independently
of predictions. No silver references in evaluation. No human-gold claims for agent
annotations. Validate rendered synthetic spans before accepting them; synthetic
examples and descendants belong only in training. Freeze test manifests after
adjudication and retain hashes. Corpus validation does not replace this audit.

Manifest v1 is an object with version=1, frozen=false/true, and entries. Entries
require id, project, leakage_group, family, split, input, annotation, raw_sha256,
command_path, tool_version, source_url, license_evidence, locale, terminal_width,
and synthetic. Paths are relative to the manifest directory, inside corpus/.
Document missing capture metadata explicitly as null. Project identity must be
stable across forks and template descendants; put those in one leakage group.
