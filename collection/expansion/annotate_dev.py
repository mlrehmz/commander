"""Materialize source-transcribed development references without model predictions."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from materialize_remaining import F, R, materialize  # noqa: E402
from helpcat.audit import audit_catalog  # noqa: E402
from helpcat.collect import atomic_write  # noqa: E402

SPECS = {
    "golang-root": {
        "command": ["gofmt"],
        "usage": [1],
        "flags": [
            F(2, "-cpuprofile", "string", R(3)),
            F(4, "-d", description=R(4)),
            F(5, "-e", description=R(5)),
            F(6, "-l", description=R(6)),
            F(7, "-r", "string", R(8)),
            F(9, "-s", description=R(9)),
            F(10, "-w", description=R(10)),
        ],
    },
    "llm-root": {
        "command": ["llm"],
        "usage": [1],
        "headings": [25, 29],
        "other": [14, 15, 19, 23],
        "flags": [F(26, "--version", description=R(26)), F(27, "-h --help", description=R(27))],
        "commands": [
            (line, name, R(line))
            for line, name in enumerate(
                "prompt* aliases chat collections embed embed-models embed-multi fragments "
                "install keys logs models openai plugins schemas similar templates tools uninstall".split(),
                30,
            )
        ],
    },
}

for identifier, spec in SPECS.items():
    packet = materialize(identifier, spec, input_directory=Path("corpus/intake/expansion/dev"))
    issues = audit_catalog(packet["reference"])
    if issues:
        raise ValueError(issues)
    atomic_write(
        f"corpus/annotations/primary/{identifier}.json",
        (json.dumps(packet, indent=2, ensure_ascii=False) + "\n").encode(),
    )
