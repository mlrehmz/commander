"""Validate authoritative capture manifests before using them."""

import hashlib
import json
from pathlib import Path

from .core import LABELS, canonicalize, validate_catalog
from .audit import audit_catalog

SPLITS = {"train", "dev", "familiar_test", "cobra_test", "clap_test"}


def load_manifest(path, *, splits=("train", "dev")):
    path = Path(path)
    data = json.loads(path.read_text())
    if data.get("version") != 1 or not isinstance(data.get("entries"), list):
        raise ValueError("unsupported manifest")
    groups, counts, hashes, raw_hashes = {}, {}, {}, {}
    required = {
        "id",
        "project",
        "leakage_group",
        "family",
        "split",
        "input",
        "annotation",
        "raw_sha256",
        "command_path",
        "tool_version",
        "source_url",
        "license_evidence",
        "locale",
        "terminal_width",
        "synthetic",
    }
    result = []
    ids = set()
    for entry in data["entries"]:
        if not required <= entry.keys() or entry["split"] not in SPLITS:
            raise ValueError("incomplete corpus metadata")
        if entry["id"] in ids:
            raise ValueError("duplicate capture id")
        ids.add(entry["id"])
        if entry["synthetic"] and entry["split"] != "train":
            raise ValueError("synthetic data outside training")
        for group in (entry["leakage_group"], "project:" + entry["project"]):
            if group in groups and groups[group] != entry["split"]:
                raise ValueError("split leakage")
            groups[group] = entry["split"]
        counts[entry["project"]] = counts.get(entry["project"], 0) + 1
        if counts[entry["project"]] > 3:
            raise ValueError("more than three invocations per project")
        if entry["family"] in ("cobra", "clap") and entry["split"] != entry["family"] + "_test":
            raise ValueError("held-out family leakage")
        if entry["split"] in ("cobra_test", "clap_test") and entry["family"] != entry[
            "split"
        ].removesuffix("_test"):
            raise ValueError("held-out track requires verified family")
        raw_hash = entry["raw_sha256"]
        if raw_hash in raw_hashes and raw_hashes[raw_hash] != entry["leakage_group"]:
            raise ValueError("duplicate content in different leakage groups")
        raw_hashes[raw_hash] = entry["leakage_group"]
        # Test files stay closed in routine development.
        if entry["split"] not in splits:
            continue

        def resolve(relative):
            resolved = (path.parent / relative).resolve()
            if not resolved.is_relative_to(path.parent.parent.resolve()):
                raise ValueError("corpus path escapes corpus root")
            return resolved

        raw = resolve(entry["input"]).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != entry["raw_sha256"]:
            raise ValueError("capture hash mismatch")
        source = canonicalize(raw.decode("utf-8"))
        canonical_hash = source["canonical_sha256"]
        if canonical_hash in hashes and hashes[canonical_hash] != entry["leakage_group"]:
            raise ValueError("duplicate content in different leakage groups")
        hashes[canonical_hash] = entry["leakage_group"]
        annotation = json.loads(resolve(entry["annotation"]).read_text())
        lines = source["canonical_text"].split("\n")
        if (
            annotation.get("canonical_sha256") != canonical_hash
            or len(annotation.get("labels", [])) != len(lines)
            or any(label not in LABELS for label in annotation["labels"])
        ):
            raise ValueError("annotation alignment mismatch")
        if not annotation.get("annotator") or annotation.get("producer") not in ("human", "agent"):
            raise ValueError("annotation identity missing")
        if not annotation.get("adjudicated") or "reference" not in annotation:
            raise ValueError("reference not adjudicated")
        reference = validate_catalog(annotation["reference"])
        if reference["source"] != source or reference["command_path"] != entry["command_path"]:
            raise ValueError("reference source or scope mismatch")
        issues = audit_catalog(reference)
        if issues:
            raise ValueError(f"reference audit failed: {issues}")
        if data.get("require_source_audit"):
            audit_path = resolve(entry["source_audit"])
            audit_bytes = audit_path.read_bytes()
            if hashlib.sha256(audit_bytes).hexdigest() != entry["source_audit_sha256"]:
                raise ValueError("source audit hash mismatch")
            audit = json.loads(audit_bytes)
            page = audit["page"]
            if (
                audit.get("no_model_predictions_used") is not True
                or not audit.get("auditor")
                or page["id"] != entry["id"]
                or page["canonical_sha256"] != source["canonical_sha256"]
                or page["adjudicated_packet_sha256"]
                != hashlib.sha256(resolve(entry["annotation"]).read_bytes()).hexdigest()
                or audit.get("audit_version") != 1
                or audit.get("producer") not in ("human", "agent")
                or page.get("remaining_source_evidence_omissions_detected") is not False
                or not {
                    "packet_validation",
                    "evidence_bounds_and_literal_fidelity",
                    "alias_token_boundaries",
                    "transformations_and_provenance",
                    "explicit_declarations_and_advertised_entries",
                    "all_line_labels_and_final_empty_line",
                }
                <= page["checks"].keys()
                or page["findings"]
                or any(v != "pass" for v in page["checks"].values())
            ):
                raise ValueError("source audit does not cover this reference")
        result.append((entry, source, annotation))
    return data, result


def require_full_corpus(data):
    expected = {"train": 36, "dev": 12, "familiar_test": 12, "cobra_test": 20, "clap_test": 20}
    for split, count in expected.items():
        projects = {
            e["project"] for e in data["entries"] if e["split"] == split and not e["synthetic"]
        }
        if len(projects) != count:
            raise ValueError(f"{split}: requires {count} real projects, found {len(projects)}")
