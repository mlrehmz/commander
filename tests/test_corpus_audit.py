import hashlib
import json
from pathlib import Path
import shutil

import pytest

from helpcat.corpus import load_manifest


@pytest.fixture
def corpus(tmp_path):
    data = json.loads(Path("corpus/manifests/pilot.json").read_text())
    entry = data["entries"][0]
    data["entries"] = [entry]
    folder = tmp_path / "manifests"
    folder.mkdir()
    for key in ("input", "annotation", "source_audit"):
        destination = (folder / entry[key]).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path("corpus/manifests") / entry[key], destination)
    path = folder / "pilot.json"
    path.write_text(json.dumps(data))
    return path, data


def test_reference_requires_matching_source_audit_hash(corpus):
    path, data = corpus
    data["entries"][0]["source_audit_sha256"] = "0" * 64
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="source audit hash"):
        load_manifest(path)


def test_reference_edit_requires_new_audit(corpus):
    path, data = corpus
    packet = path.parent / data["entries"][0]["annotation"]
    annotation = json.loads(packet.read_text())
    annotation["notes"].append("new revision")
    packet.write_text(json.dumps(annotation))
    with pytest.raises(ValueError, match="source audit does not cover"):
        load_manifest(path)


def test_empty_audit_checks_cannot_qualify(corpus):
    path, data = corpus
    audit_path = path.parent / data["entries"][0]["source_audit"]
    audit = json.loads(audit_path.read_text())
    audit["page"]["checks"] = {}
    audit_path.write_text(json.dumps(audit))
    data["entries"][0]["source_audit_sha256"] = hashlib.sha256(audit_path.read_bytes()).hexdigest()
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="source audit does not cover"):
        load_manifest(path)
