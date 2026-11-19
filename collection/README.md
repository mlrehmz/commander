# Collection pilot

Ten pinned projects; one root-help invocation each. `survey.json` separates intake
from the still-empty adjudicated corpus manifest. Unknown survey fields are null
or explicitly unknown, not unsupported claims of absence. No family adapter is
approved. Ten projects are not the target 100-project dataset.

The container base is pinned by digest, all 88 dependency versions and wheel
hashes are locked, and installation accepts binary wheels only. Downloads happen
during environment preparation. Actual help calls run offline and non-root with
a read-only root, temporary writable storage and CPU/memory/PID/time/output limits.
The collector never invokes a harvested executable directly on the host.

```sh
podman build --pull=never -t localhost/helpcat-collection:reproduction -f collection/Containerfile collection
# Inspect the resulting full local image ID and place sha256:<ID> in a new plan.
podman image inspect localhost/helpcat-collection:reproduction --format '{{.Id}}'
uv run python -m helpcat.collect --plan collection/plan.json --output /tmp/helpcat-recapture
```

Pull the exact Containerfile base digest first if absent. `plan.json` preserves
the actual original image ID and nine successful captures; Datasette used
`datasette-retry-plan.json` with compatible Setuptools. New builds can have a new
local ID even with the same inputs; create a new plan rather than altering the
historical receipts. Retry plans must target a fresh output folder if the image
or capture bytes differ. Existing successful captures cannot be overwritten with
different data. Failed attempts keep separate receipts and do not block retry.

`licenses.json` contains exact notices from the installed primary packages;
`package-metadata.json` preserves publisher metadata. To reproduce notices:
`uv run python collection/read_licenses.py sha256:<FULL_IMAGE_ID>`.
`verify_sandbox.py` runs inside the collection image; the recorded probe confirmed
UID, root mount, loopback-only interfaces and cgroup limits. Metadata receipts are
not a substitute for annotation or a family/leakage audit.

The generic collector limits combined stdout/stderr to 1 MiB and each help process
to 20 seconds. It records nonzero exits explicitly, removes containers on failure,
and atomically writes authoritative captures. Its process tests use only locally
authored fake runtime scripts. Actual Podman execution was checked separately.

All ten captures now have primary/blind agent annotations, recorded source
adjudications and a source-only audit. The adjudicator corrected draft errors;
drafts remain immutable. Reproduce the eight additional primary packets and
recorded decisions with `materialize_remaining.py` and `adjudicate_remaining.py`.
`curate_pilot.py` verifies the audit, creates per-page audit shards and updates the
training-only manifest. It cannot update a frozen manifest. Corpus loading checks
both audit and exact annotation hashes; edits require re-audit. Unknown formatter
families remain unknown; this is not the completed 100-project survey.
