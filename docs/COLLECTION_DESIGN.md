# Collection pilot scaffold

Entry point: `python -m helpcat.collect --plan collection/plan.json`.
A reviewed plan owns the image digest, commands and project metadata. The
collector owns bounded subprocess pipes and atomically stored captures plus
receipts. It invokes only the container runtime on the host, never harvested CLIs.
Network access is permitted for obtaining the pinned image and wheel artifacts;
help invocations run with no network, read-only root, temporary /tmp, non-root
UID, no capabilities and explicit time, memory, CPU, PID and output limits.

Normal path: validate plan -> construct runtime argv -> bounded capture -> write
capture and provenance receipt atomically. Failure path: kill runtime on timeout
or excessive output -> keep diagnostic receipt without a usable capture. A retry
must not overwrite an existing capture with different bytes. Identical bytes are
idempotent. The image must be addressed by digest or full local image ID.

Tests at the collector public boundary cover limits and actual process cleanup,
argv safety and receipt hashes. A locally authored fake runtime verifies process
I/O failures without executing harvested code. A real Podman pilot separately
checks the runtime boundary. Captures remain intake material until license review,
family grouping, annotations, blind audit and split assignment are complete.

Expansion needs explicitly reviewed capture streams and exit codes: some standard
help printers use stderr or return 2 for help. The collector must not guess a stream
or treat arbitrary nonzero exits as success. Plans may name stdout/stderr and exact
accepted codes; time/output/resource failures remain failures. Record both stream
hashes and the actual exit code, then normalize/hash only the selected text. Empty
selected output is a failed capture. Tests use authored fake runtimes, including an
unaccepted exit and empty output. Existing plans retain stdout/zero defaults.
