# Dataset datasheet — collection pilot

Ten distinct projects have root-help captures in `corpus/intake` (973 canonical
lines, counting the final empty lines). All captures have hashes and receipts.
Exact publisher license notices are preserved in `collection/licenses.json`.
SQLFluff and Hatch each have independent primary and blind agent annotations.
Their extracted records and evidence agree exactly. Five SQLFluff markup/example
label disagreements were resolved against source with recorded decisions; Hatch
has no disagreements. Both adjudicated references are in the training pilot
manifest. The other eight intake pages await primary annotation. Final independent
dataset audit, full grouping and split freeze remain open. These are agent
references, not human gold; no development or test examples are admitted yet.
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
surface survey fields, eight remaining primary annotations, final audit, leakage
review and split freeze remain open. Rich CLI's banner says v1.8.0 although the
installed wheel metadata says 1.8.1; both are preserved. COLUMNS=80 is requested;
renderer output widths can differ because captures have no TTY.
