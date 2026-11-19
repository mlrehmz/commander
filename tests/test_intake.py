import hashlib
import json
from pathlib import Path

from helpcat.annotation import validate_pass
from helpcat.core import canonicalize


def test_intake_hashes_receipts_and_license_notices():
    inventory = json.loads(Path("collection/survey.json").read_text())
    licensed = {
        r["package"]
        for r in json.loads(Path("collection/licenses.json").read_text())
        if r["notices"]
    }
    for entry in inventory["projects"]:
        raw = Path(entry["input"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == entry["raw_sha256"]
        receipt = json.loads(Path(entry["receipt"]).read_text())
        assert receipt["status"] == "ok"
        assert receipt["sha256"] == entry["raw_sha256"]
        assert receipt["project"] in licensed
        assert "--network=none" in receipt["runtime_argv"]
        assert entry["split"] in (None, "train")
        canonicalize(raw.decode("utf-8"))
        if entry["primary_annotation"]:
            packet = validate_pass(json.loads(Path(entry["primary_annotation"]).read_text()))
            assert not packet["adjudicated"]
            assert not packet["blind"]
            assert packet["source"]["raw_sha256"] == entry["raw_sha256"]


def test_adjudicated_pilot_has_auditable_distinct_blind_passes():
    from helpcat.corpus import load_manifest

    data, pages = load_manifest("corpus/manifests/pilot.json")
    assert len(pages) == 2
    assert not data["frozen"]
    assert all(entry["split"] == "train" for entry, _, _ in pages)
    for entry, source, annotation in pages:
        report = json.loads(
            Path("corpus/annotations/adjudication", entry["id"] + ".json").read_text()
        )
        assert len(set(report["annotators"])) == 2
        assert report["adjudicated"]
        assert annotation["adjudicated"]
        assert annotation["blind_pass"]["blind"]
        assert source["canonical_sha256"] == report["canonical_sha256"]
