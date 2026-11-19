"""Source-only annotation packets and blind-pass comparison."""

import argparse
import json
from pathlib import Path

from .collect import atomic_write
from .core import LABELS, canonicalize, validate_catalog


def annotation_packet(text, command_path, *, annotator, producer):
    if not annotator or producer not in ("agent", "human"):
        raise ValueError("annotation identity and producer are required")
    source = canonicalize(text)
    return {
        "annotation_version": 1,
        "canonical_sha256": source["canonical_sha256"],
        "command_path": list(command_path),
        "source": source,
        "annotator": annotator,
        "producer": producer,
        "blind": False,
        "labels": [None] * len(source["canonical_text"].split("\n")),
        "reference": None,
        "adjudicated": False,
        "notes": [],
    }


def validate_pass(packet):
    if packet.get("annotation_version") != 1:
        raise ValueError("unsupported annotation version")
    if not packet.get("annotator") or packet.get("producer") not in ("agent", "human"):
        raise ValueError("missing annotation identity")
    source = packet["source"]
    rebuilt = canonicalize(source["canonical_text"])
    if (
        rebuilt["canonical_sha256"] != packet["canonical_sha256"]
        or source["canonical_sha256"] != packet["canonical_sha256"]
    ):
        raise ValueError("annotation hash mismatch")
    if (
        len(packet["labels"]) != len(source["canonical_text"].split("\n"))
        or any(label not in LABELS for label in packet["labels"])
        or packet["reference"] is None
    ):
        raise ValueError("incomplete annotation")
    reference = validate_catalog(packet["reference"])
    if reference["source"] != source or reference["command_path"] != packet["command_path"]:
        raise ValueError("reference source or scope mismatch")
    return packet


def compare_passes(primary, blind):
    validate_pass(primary)
    validate_pass(blind)
    if not blind.get("blind") or primary["annotator"] == blind["annotator"]:
        raise ValueError("blind pass requires a distinct annotator")
    if primary["source"] != blind["source"] or primary["command_path"] != blind["command_path"]:
        raise ValueError("blind passes have different sources or scopes")
    disagreements = []
    for n, (a, b) in enumerate(zip(primary["labels"], blind["labels"]), 1):
        if a != b:
            disagreements.append({"kind": "line_label", "line": n, "primary": a, "blind": b})
    for kind in ("flags", "subcommands", "positionals"):
        # Compare evidence and values; scores are not annotation truth.
        def records(packet):
            return [
                {k: v for k, v in r.items() if k != "selection_score"}
                for r in packet["reference"][kind]
            ]

        if records(primary) != records(blind):
            disagreements.append(
                {"kind": kind, "primary": records(primary), "blind": records(blind)}
            )
    return {
        "canonical_sha256": primary["canonical_sha256"],
        "annotators": [primary["annotator"], blind["annotator"]],
        "disagreements": disagreements,
        "adjudicated": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="operation", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("capture")
    prepare.add_argument("--command", action="append", required=True)
    prepare.add_argument("--annotator", required=True)
    prepare.add_argument("--producer", choices=["agent", "human"], required=True)
    prepare.add_argument("--output", required=True)
    compare = sub.add_parser("compare")
    compare.add_argument("primary")
    compare.add_argument("blind")
    args = parser.parse_args(argv)
    try:
        if args.operation == "prepare":
            packet = annotation_packet(
                Path(args.capture).read_bytes().decode("utf-8"),
                tuple(args.command),
                annotator=args.annotator,
                producer=args.producer,
            )
            atomic_write(
                args.output, (json.dumps(packet, indent=2, ensure_ascii=False) + "\n").encode()
            )
            return 0
        report = compare_passes(
            json.loads(Path(args.primary).read_text()), json.loads(Path(args.blind).read_text())
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1 if report["disagreements"] else 0
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(2, f"annotation: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
