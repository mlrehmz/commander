"""Development gates. Final evaluation is deliberately inaccessible here."""

import argparse
import json
import sys
from pathlib import Path

from .core import validate_catalog
from .corpus import load_manifest, require_full_corpus
from .parser import ParserEngine, assemble


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


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["validate", "assembler-gate", "train-crf", "final"])
    parser.add_argument("--manifest", default="corpus/manifests/pilot.json")
    parser.add_argument("--output", default="artifacts/crf.model")
    args = parser.parse_args(argv)
    try:
        if args.operation == "final":
            raise ValueError(
                "Final evaluation unavailable: corpus, calibration and engine freeze are incomplete"
            )
        data, pages = load_manifest(args.manifest)
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
