"""Record source-based decisions for the first two blind comparisons."""

import copy
import hashlib
import json
from pathlib import Path

from helpcat.annotation import compare_passes, validate_pass
from helpcat.collect import atomic_write

DECISIONS = {
    "sqlfluff-root": {
        21: "The RST code-block directive is markup, not prose: label other.",
        23: "This is a shell invocation example, not prose: label other.",
        25: "This is a shell invocation example, not prose: label other.",
        27: "This is a shell invocation example, not prose: label other.",
        29: "This is a shell invocation example, not prose: label other.",
    },
    "hatch-root": {},
}


def main():
    for identifier, decisions in DECISIONS.items():
        primary_path = Path(f"corpus/annotations/primary/{identifier}.json")
        blind_path = Path(f"corpus/annotations/blind/{identifier}.json")
        primary = json.loads(primary_path.read_text())
        blind = json.loads(blind_path.read_text())
        report = compare_passes(primary, blind)
        if any(d["kind"] != "line_label" for d in report["disagreements"]):
            raise ValueError("unreviewed record disagreement")
        if {d["line"] for d in report["disagreements"]} != set(decisions):
            raise ValueError("disagreements changed; new source review required")
        adjudicated = copy.deepcopy(primary)
        for d in report["disagreements"]:
            if d["primary"] != "prose" or d["blind"] != "other":
                raise ValueError("reviewed labels changed")
            adjudicated["labels"][d["line"] - 1] = "other"
            d.update(decision="other", justification=decisions[d["line"]])
        report.update(
            adjudicated=True,
            adjudicator="codex-primary-2026-11-19",
            primary_sha256=hashlib.sha256(primary_path.read_bytes()).hexdigest(),
            blind_sha256=hashlib.sha256(blind_path.read_bytes()).hexdigest(),
            record_agreement="All flag, advertised-entry, semantic and evidence fields match.",
            producer="agent",
        )
        adjudicated.update(
            adjudicated=True,
            adjudicator=report["adjudicator"],
            blind_pass={
                "annotator": blind["annotator"],
                "producer": blind["producer"],
                "blind": True,
                "path": str(blind_path),
            },
            notes=[
                "Agent-produced reference, not human gold.",
                "Blind record values and evidence agree exactly.",
                "Source-based line-label decisions are in adjudication report.",
                "Final independent dataset audit remains pending.",
            ],
        )
        validate_pass(adjudicated)
        for folder, data in [("adjudicated", adjudicated), ("adjudication", report)]:
            atomic_write(
                f"corpus/annotations/{folder}/{identifier}.json",
                (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode(),
            )
        print(identifier, "adjudicated;", len(decisions), "source-based decisions")


if __name__ == "__main__":
    main()
