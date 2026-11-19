"""Materialize source-reviewed primary annotations; this does not run a parser.

The declarations and line labels below were transcribed by the primary agent.
These are single-pass agent references, pending blind review and adjudication.
"""

import json
from pathlib import Path

from helpcat.annotation import annotation_packet, validate_pass
from helpcat.core import field
from helpcat.collect import atomic_write

TRANSCRIPTIONS = {
    "sqlfluff-root": {
        "command": ["sqlfluff"],
        "usage": [1],
        "headings": [5, 9, 19],
        "flags": [(6, ["--version"], None, [6]), (7, ["-h", "--help"], None, [7])],
        "commands": [
            (10, "dialects"),
            (11, "fix"),
            (12, "format"),
            (13, "lint"),
            (14, "parse"),
            (15, "render"),
            (16, "rules"),
            (17, "version"),
        ],
        "other": [],
    },
    "hatch-root": {
        "command": ["hatch"],
        "usage": [1],
        "headings": [10, 35],
        "flags": [
            (11, ["-e", "--env"], "TEXT", [11, 12]),
            (13, ["-p", "--project"], "TEXT", [13, 14]),
            (15, ["-v", "--verbose"], None, [15, 16]),
            (17, ["-q", "--quiet"], None, [17, 18]),
            (19, ["--color", "--no-color"], None, [19, 20, 21]),
            (22, ["--interactive", "--no-interactive"], None, [23, 24, 25]),
            (26, ["--data-dir"], "TEXT", [26, 27]),
            (28, ["--cache-dir"], "TEXT", [28, 29]),
            (30, ["--config"], "TEXT", [30, 31]),
            (32, ["--version"], None, [32]),
            (33, ["-h", "--help"], None, [33]),
        ],
        "commands": [
            (36, "build"),
            (37, "clean"),
            (38, "config"),
            (39, "dep"),
            (40, "env"),
            (41, "fmt"),
            (42, "new"),
            (43, "project"),
            (44, "publish"),
            (45, "python"),
            (46, "run"),
            (47, "self"),
            (48, "shell"),
            (49, "status"),
            (50, "test"),
            (51, "version"),
        ],
        "other": [3, 4, 5, 6, 7, 8],
    },
}


def materialize(identifier, spec):
    raw = Path(f"corpus/intake/{identifier}.txt").read_bytes()
    packet = annotation_packet(
        raw.decode("utf-8"),
        tuple(spec["command"]),
        annotator="codex-primary-2026-11-19",
        producer="agent",
    )
    lines = packet["source"]["canonical_text"].split("\n")
    labels = ["blank" if not line.strip() else "prose" for line in lines]
    for label, numbers in [
        ("usage", spec["usage"]),
        ("section_heading", spec["headings"]),
        ("other", spec["other"]),
    ]:
        for n in numbers:
            labels[n - 1] = label

    def literal(n, word):
        start = lines[n - 1].index(word)
        return field(lines, [(n, start, start + len(word))])

    reference = {
        "schema_version": "1.0",
        "source": packet["source"],
        "command_path": spec["command"],
        "flags": [],
        "subcommands": [],
        "positionals": [],
        "status": "ok",
        "diagnostics": [],
        "engine": {
            "name": "manual-agent-annotation",
            "version": "primary-1",
            "threshold": 0.0,
            "calibrated": False,
        },
    }
    for n, aliases, meta, description_lines in spec["flags"]:
        labels[n - 1] = "option_declaration"
        declaration_end = (
            lines[n - 1].index(meta) + len(meta)
            if meta
            else max(lines[n - 1].index(a) + len(a) for a in aliases)
        )
        spans = []
        for dn in description_lines:
            line = lines[dn - 1]
            start = len(line) - len(line.lstrip())
            if dn == n:
                start = (
                    declaration_end
                    + len(line[declaration_end:])
                    - len(line[declaration_end:].lstrip())
                )
            else:
                labels[dn - 1] = "description_continuation"
            spans.append((dn, start, len(line.rstrip())))
        description = field(lines, spans)
        if len(spans) > 1:
            description = field(
                lines,
                spans,
                value=" ".join(description["literal"].split()),
                rule="join-description-whitespace",
            )
        reference["flags"].append(
            {
                "aliases": [literal(n, a) for a in aliases],
                "metavar": literal(n, meta) if meta else None,
                "arity": field(
                    lines,
                    [(n, lines[n - 1].index(meta), lines[n - 1].index(meta) + len(meta))],
                    value="required",
                    rule="declaration-value-notation",
                )
                if meta
                else None,
                "takes_value": True if meta else None,
                "required_presence": None,
                "type": None,
                "default": None,
                "choices": None,
                "description": description,
                "selection_score": 1.0,
            }
        )
    for n, name in spec["commands"]:
        labels[n - 1] = "subcommand_declaration"
        end = lines[n - 1].index(name) + len(name)
        start = end + len(lines[n - 1][end:]) - len(lines[n - 1][end:].lstrip())
        reference["subcommands"].append(
            {
                "name": literal(n, name),
                "description": field(lines, [(n, start, len(lines[n - 1].rstrip()))]),
                "selection_score": 1.0,
            }
        )
    packet.update(
        labels=labels,
        reference=reference,
        notes=[
            "Single primary source pass. No parser predictions used.",
            "Unknown semantic fields remain unknown; no blind pass or adjudication yet.",
        ],
    )
    validate_pass(packet)
    return packet


if __name__ == "__main__":
    folder = Path("corpus/annotations/primary")
    folder.mkdir(parents=True, exist_ok=True)
    for identifier, spec in TRANSCRIPTIONS.items():
        packet = materialize(identifier, spec)
        atomic_write(
            folder / (identifier + ".json"),
            (json.dumps(packet, indent=2, ensure_ascii=False) + "\n").encode(),
        )
        print(identifier, len(packet["reference"]["flags"]), "flag records; pending blind review")
