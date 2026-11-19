"""Apply recorded source decisions to immutable primary and blind drafts."""

import copy
import hashlib
import json
from pathlib import Path

from helpcat.annotation import compare_passes, validate_pass
from helpcat.audit import audit_catalog
from helpcat.collect import atomic_write

REASONS = {
    "default": "The source explicitly advertises this literal default. Preserve its string value; do not infer a Python type or reinterpret explicit None as unknown.",
    "choices": "The source explicitly lists these alternatives. Preserve the literal list with its evidence; do not infer value optionality from square-bracketed alternatives.",
    "aliases": "The primary spans select separately advertised tokens. Matching a short alias inside a long flag is not evidence for the short declaration.",
    "metavar": "Both repeated value notations support the same value. Use the occurrence following the last explicitly grouped alias.",
    "arity": "Keep uncertainty for bracketed pipe alternatives; otherwise retain the supported notation and its evidence following the last grouped alias.",
    "takes_value": "This field follows adjudicated arity. Unknown arity must remain null.",
    "description": "The primary selects only description text, excluding declaration syntax. Collapse all whitespace in normalized wrapped values while preserving exact literals and spans.",
}


def main():
    config = json.loads(Path("collection/pilot-review-decisions.json").read_text())
    for identifier, policy in config["pages"].items():

        def read(pass_name):
            path = Path(f"corpus/annotations/{pass_name}/{identifier}.json")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != policy[pass_name + "_sha256"]:
                raise ValueError("reviewed draft changed; new source adjudication required")
            return json.loads(path.read_text())

        primary, blind = read("primary"), read("blind")
        comparison = compare_passes(primary, blind)
        result = copy.deepcopy(primary)
        decisions = []
        seen_lines = set()
        for difference in comparison["disagreements"]:
            kind = difference["kind"]
            if kind == "line_label":
                line = str(difference["line"])
                if line not in policy["line_decisions"]:
                    raise ValueError("unreviewed line disagreement")
                label = policy["line_decisions"][line]
                result["labels"][int(line) - 1] = label
                seen_lines.add(line)
                decisions.append(
                    {
                        "kind": "line_label",
                        "line": int(line),
                        "decision": label,
                        "justification": "Runtime/config notices are other; the trailing HTTPie suggestions sentence is prose, not a help section.",
                    }
                )
                continue
            if len(difference["primary"]) != len(difference["blind"]):
                raise ValueError("unreviewed record identity disagreement")
            for index, (a, b) in enumerate(zip(difference["primary"], difference["blind"])):
                if kind == "flags" and [x["value"] for x in a["aliases"]] != [
                    x["value"] for x in b["aliases"]
                ]:
                    raise ValueError("unreviewed alias grouping disagreement")
                for key in a:
                    if a[key] == b[key]:
                        continue
                    if key not in policy["field_decisions"]:
                        raise ValueError(
                            f"unreviewed field disagreement: {identifier} {kind} {key}"
                        )
                    choice = policy["field_decisions"][key]
                    result["reference"][kind][index][key] = copy.deepcopy(
                        a[key] if choice == "primary" else b[key]
                    )
                    decisions.append(
                        {
                            "kind": kind,
                            "record": index,
                            "field": key,
                            "decision": choice,
                            "justification": REASONS[key],
                        }
                    )
        if seen_lines != set(policy["line_decisions"]):
            raise ValueError("reviewed label disagreements changed")
        result.update(
            adjudicated=True,
            adjudicator="codex-primary-2026-11-19",
            blind_pass={
                "annotator": blind["annotator"],
                "producer": blind["producer"],
                "blind": True,
                "path": f"corpus/annotations/blind/{identifier}.json",
            },
            notes=[
                "Agent-produced reference, not human gold.",
                "Primary and blind passes agree on all extracted identities.",
                "Source-based field and label decisions are preserved in the report.",
                "No parser predictions were used to create or adjudicate this reference.",
            ],
        )
        validate_pass(result)
        issues = audit_catalog(result["reference"])
        if issues:
            raise ValueError(f"adjudicated reference fails audit: {issues}")
        report = {
            **comparison,
            "adjudicated": True,
            "producer": "agent",
            "adjudicator": result["adjudicator"],
            "primary_sha256": policy["primary_sha256"],
            "blind_sha256": policy["blind_sha256"],
            "decisions": decisions,
            "primary_audit_issues": audit_catalog(primary["reference"]),
            "blind_audit_issues": audit_catalog(blind["reference"]),
            "adjudicated_audit_issues": issues,
        }
        for folder, data in [("adjudicated", result), ("adjudication", report)]:
            atomic_write(
                f"corpus/annotations/{folder}/{identifier}.json",
                (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode(),
            )
        print(identifier, "adjudicated;", len(decisions), "recorded source decisions")


if __name__ == "__main__":
    main()
