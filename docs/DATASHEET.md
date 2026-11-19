# Dataset datasheet — collection pilot

Ten distinct projects have root-help captures in `corpus/intake` (973 canonical
lines, counting the final empty lines). All captures have hashes and receipts.
Exact publisher license notices are preserved in `collection/licenses.json`.
All ten projects now have separate primary and blind agent annotations, source-based
adjudications and an independent-of-model-predictions source audit. The auditor had
performed the blind pass; this relationship is explicit in the audit report.
Both sets of drafts remain unchanged even where their evidence was wrong. Final
references correct short-alias substring errors, description boundaries, whitespace
normalization and conservative semantics through recorded decisions.

The training pilot manifest contains ten audited references: 205 flag records,
290 advertised flag spellings, 85 advertised command spellings, and four positional
records. All 973 canonical lines have labels. The manifest is unfrozen and training
only; no development or test pages are admitted. Family labels remain unknown
pending source verification and the wider survey. These are agent references, not
human gold. Final full-dataset grouping, review and split freeze remain open.
The pilot does not establish accuracy, family transfer or any experimental gate.
Tests also use original miniature strings. The full target remains 100 projects.

Collection must record permissions before redistribution. Prefer committed help
snapshots or reproducible formatter fixtures. Host execution of harvested tools
is forbidden; collection needing execution requires the exact isolated container
controls in SPEC.md. The collector is implemented. Only the constrained container runtime executes
harvested CLIs; none run directly on the host. The container uses pinned binary
wheels and a digest-pinned base. CLI execution has no network access; image and
wheel downloads occur during environment preparation. A sandbox probe verified
actual cgroup/mount/UID/network settings (collection/sandbox-verification.json).
Datasette's first attempt failed due to missing pkg_resources; its receipt is
retained and a Setuptools-pinned retry succeeded. Family verification, remaining
surface survey fields, the rest of the 100-project corpus, full-dataset audit, leakage
review and split freeze remain open. Rich CLI's banner says v1.8.0 although the
installed wheel metadata says 1.8.1; both are preserved. COLUMNS=80 is requested;
renderer output widths can differ because captures have no TTY.
