"""Development gates. Final evaluation is deliberately inaccessible here."""

import argparse
import json
import sys
from pathlib import Path

from .core import validate_catalog
from .corpus import load_manifest, require_full_corpus
from .parser import ParserEngine, assemble, parse_help
from .audit import audit_catalog


def identities(catalog):
    return {
        (tuple(catalog["command_path"]), alias["value"])
        for flag in catalog["flags"]
        for alias in flag["aliases"]
    }


def flag_counts(prediction, reference):
    expected, actual = identities(reference), identities(prediction)
    return {
        "tp": len(actual & expected),
        "fp": len(actual - expected),
        "fn": len(expected - actual),
    }


def rates(counts):
    tp, fp, fn = (counts[k] for k in ("tp", "fp", "fn"))
    return {
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "accepted": tp + fp,
    }


def assembler_gate(pages):
    totals = dict(tp=0, fp=0, fn=0)
    per_page = []
    for entry, source, annotation in pages:
        reference = validate_catalog(annotation["reference"])
        if reference["command_path"] != entry["command_path"] or reference["source"] != source:
            raise ValueError("reference source or scope mismatch")
        prediction = assemble(
            source,
            tuple(entry["command_path"]),
            [(label, 1.0) for label in annotation["labels"]],
            ParserEngine(),
        )
        counts = flag_counts(prediction, reference)
        for key in totals:
            totals[key] += counts[key]
        per_page.append({"id": entry["id"], **counts})
    metrics = rates(totals)
    passed = (
        bool(pages)
        and metrics["precision"] is not None
        and metrics["recall"] is not None
        and metrics["precision"] >= 0.99
        and metrics["recall"] >= 0.90
    )
    return {
        "gate": "assembler",
        "passed": passed,
        "pages": len(pages),
        **totals,
        **metrics,
        "per_page": per_page,
    }


def pilot_diagnostic(pages):
    if any(entry["split"] != "train" for entry, _, _ in pages):
        raise ValueError("pilot diagnostics accept training pages only")
    engines = {
        name: {
            "counts": dict(tp=0, fp=0, fn=0),
            "flag_records": 0,
            "exact_alias_groups": 0,
            "evidence_audit_issues": 0,
        }
        for name in ("oracle", "rules")
    }
    rows = []
    for entry, source, annotation in pages:
        reference = validate_catalog(annotation["reference"])
        if audit_catalog(reference):
            raise ValueError("pilot reference fails evidence audit")
        command = tuple(entry["command_path"])
        predictions = {
            "oracle": assemble(
                source, command, [(label, 1.0) for label in annotation["labels"]], ParserEngine()
            ),
            "rules": parse_help(
                source["canonical_text"], command_path=command, engine=ParserEngine()
            ),
        }
        row = {
            "id": entry["id"],
            "canonical_sha256": source["canonical_sha256"],
            "reference_records": len(reference["flags"]),
            "reference_spellings": len(identities(reference)),
        }
        expected_groups = {frozenset(a["value"] for a in f["aliases"]) for f in reference["flags"]}
        for name, prediction in predictions.items():
            counts = flag_counts(prediction, reference)
            for key, value in counts.items():
                engines[name]["counts"][key] += value
            groups = {frozenset(a["value"] for a in f["aliases"]) for f in prediction["flags"]}
            issues = audit_catalog(prediction)
            engines[name]["flag_records"] += len(prediction["flags"])
            engines[name]["exact_alias_groups"] += len(groups & expected_groups)
            engines[name]["evidence_audit_issues"] += len(issues)
            expected = identities(reference)
            actual = identities(prediction)
            row[name] = {
                "counts": counts,
                "status": prediction["status"],
                "flag_records": len(prediction["flags"]),
                "exact_alias_groups": len(groups & expected_groups),
                "missed_spellings": sorted(spelling for _, spelling in expected - actual),
                "false_spellings": sorted(spelling for _, spelling in actual - expected),
                "diagnostics": prediction["diagnostics"],
                "evidence_audit_issues": issues,
            }
        rows.append(row)
    for result in engines.values():
        metrics = rates(result["counts"])
        metrics["accepted_spellings"] = metrics.pop("accepted")
        result["metrics"] = metrics
    return {
        "report_version": 1,
        "training_pilot_only": True,
        "release_qualified": False,
        "development_gate_evaluated": False,
        "pages": len(pages),
        "reference_records": sum(row["reference_records"] for row in rows),
        "reference_spellings": sum(row["reference_spellings"] for row in rows),
        "limitations": [
            "Training examples were used to fix the assembler; this is a regression diagnostic.",
            "No development/test track, calibrated model, confidence interval or release selection is evaluated.",
        ],
        **engines,
        "per_page": rows,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "operation",
        choices=["validate", "pilot-diagnostic", "assembler-gate", "train-crf", "final"],
    )
    parser.add_argument("--manifest", default="corpus/manifests/pilot.json")
    parser.add_argument("--output", default="artifacts/crf.model")
    args = parser.parse_args(argv)
    try:
        if args.operation == "final":
            raise ValueError(
                "Final evaluation unavailable: corpus, calibration and engine freeze are incomplete"
            )
        data, pages = load_manifest(
            args.manifest,
            splits=("train",) if args.operation == "pilot-diagnostic" else ("train", "dev"),
        )
        if args.operation == "pilot-diagnostic":
            import hashlib
            import subprocess

            report = pilot_diagnostic(pages)
            report["manifest_sha256"] = hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest()
            root = Path(__file__).parent
            report["code_sha256"] = {
                name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                for name in ("core.py", "parser.py", "audit.py", "experiment.py")
            }
            try:
                report["base_revision"] = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
                ).strip()
                report["working_tree_dirty"] = bool(
                    subprocess.check_output(["git", "status", "--porcelain"], text=True)
                )
            except (OSError, subprocess.SubprocessError):
                report["base_revision"] = None
                report["working_tree_dirty"] = None
            print(json.dumps(report, indent=2))
            return 0
        if args.operation == "validate":
            print(
                json.dumps(
                    {
                        "entries": len(data["entries"]),
                        "training_pages": sum(entry["split"] == "train" for entry, _, _ in pages),
                        "development_pages": sum(entry["split"] == "dev" for entry, _, _ in pages),
                    }
                )
            )
            return 0
        dev = [p for p in pages if p[0]["split"] == "dev"]
        gate = assembler_gate(dev)
        if args.operation == "assembler-gate":
            print(json.dumps(gate, indent=2))
            return 0 if gate["passed"] else 1
        require_full_corpus(data)
        if not gate["passed"]:
            raise ValueError("assembler gate has not passed")
        from .crf import train_crf

        train = [
            (source["canonical_text"].split("\n"), ann["labels"])
            for entry, source, ann in pages
            if entry["split"] == "train"
        ]
        train_crf(train, Path(args.output))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"helpcat experiment: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
