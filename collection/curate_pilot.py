"""Admit the independently audited ten-page pilot as training-only data."""

import hashlib
import json
import os
from pathlib import Path
import tempfile

from helpcat.annotation import validate_pass
from helpcat.audit import audit_catalog
from helpcat.collect import atomic_write


def main():
    inventory = json.loads(Path("collection/survey.json").read_text())
    report_path = Path("corpus/annotations/audit/pilot-independent.json")
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes)
    report_hash = hashlib.sha256(report_bytes).hexdigest()
    if not report["no_model_predictions_used"] or report["producer"] != "agent":
        raise ValueError("unexpected audit provenance")
    reviewed = {p["id"]: p for p in report["pages"]}
    if set(reviewed) != {e["id"] for e in inventory["projects"]}:
        raise ValueError("audit does not cover complete pilot")
    entries = []
    shards = []
    for item in inventory["projects"]:
        identifier = item["id"]
        page = reviewed[identifier]
        annotation_path = Path(f"corpus/annotations/adjudicated/{identifier}.json")
        annotation = validate_pass(json.loads(annotation_path.read_text()))
        if not annotation["adjudicated"] or audit_catalog(annotation["reference"]):
            raise ValueError("reference is not adjudicated and audited")
        packet_hash = hashlib.sha256(annotation_path.read_bytes()).hexdigest()
        if (
            packet_hash != page["adjudicated_packet_sha256"]
            or annotation["canonical_sha256"] != page["canonical_sha256"]
            or page["findings"]
            or any(v != "pass" for v in page["checks"].values())
        ):
            raise ValueError("source audit mismatch or unresolved findings")
        shard = {
            k: report[k]
            for k in (
                "audit_version",
                "auditor",
                "producer",
                "date",
                "no_model_predictions_used",
                "independence_statement",
            )
        }
        shard.update(source_report_sha256=report_hash, page=page)
        shard_bytes = (json.dumps(shard, indent=2, ensure_ascii=False) + "\n").encode()
        shard_path = Path(f"corpus/annotations/audit/{identifier}.json")
        shards.append((shard_path, shard_bytes))
        receipt = json.loads(Path(item["receipt"]).read_text())
        entry = {
            k: receipt[k]
            for k in (
                "id",
                "project",
                "leakage_group",
                "family",
                "command_path",
                "tool_version",
                "source_url",
                "locale",
                "terminal_width",
                "synthetic",
            )
        }
        entry.update(
            split="train",
            input=f"../intake/{identifier}.txt",
            annotation=f"../annotations/adjudicated/{identifier}.json",
            raw_sha256=receipt["sha256"],
            license_evidence="../../collection/licenses.json",
            source_audit=f"../annotations/audit/{identifier}.json",
            source_audit_sha256=hashlib.sha256(shard_bytes).hexdigest(),
        )
        entries.append(entry)
        item.update(
            primary_annotation=f"corpus/annotations/primary/{identifier}.json",
            annotation_status="independently_audited_agent_reference",
            split="train",
        )
    for path, content in shards:
        atomic_write(path, content)
    manifest = Path("corpus/manifests/pilot.json")
    if json.loads(manifest.read_text()).get("frozen"):
        raise ValueError("cannot update frozen manifest")
    payload = {"version": 1, "frozen": False, "require_source_audit": True, "entries": entries}

    def replace(path, data):
        fd, temporary = tempfile.mkstemp(dir=path.parent)
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump(data, stream, indent=2, ensure_ascii=False)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    replace(manifest, payload)
    replace(Path("collection/survey.json"), inventory)
    print("Admitted", len(entries), "source-audited training pages; no development/test data.")


if __name__ == "__main__":
    main()
