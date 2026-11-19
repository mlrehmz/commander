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
