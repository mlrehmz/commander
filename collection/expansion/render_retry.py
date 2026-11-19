"""Render three recorded terminal streams as compatible plain-text captures."""

import hashlib
import json
from pathlib import Path
import re

from helpcat.collect import atomic_write
from helpcat.core import canonicalize

for name, split in [("pip-tools", "train"), ("awscli", "dev"), ("less", "dev")]:
    root = Path("corpus/intake/expansion") / split
    evidence = json.loads(
        Path(f"collection/expansion/{name}-root-failure-evidence.json").read_text()
    )
    raw = Path(evidence["selected_stream_file"]).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != evidence["raw_sha256"]:
        raise ValueError("Original capture hash mismatch")
    source = raw.decode("utf-8")
    if name == "pip-tools":
        rendered = re.sub(r"(?<=\n)\x08(?=\n)", "", source)
        rule = "ignore cursor-left at start of line"
    elif name == "awscli":
        rendered = source.replace("+\x08o", "o")
        rule = "render groff bullet overstrike as its last glyph"
    else:
        rendered = re.sub(r"_\x08([^\n\r\x08])|([^\n\r\x08])\x08\2", r"\1\2", source)
        rule = "render underlined or repeated nroff glyph once"
    normalized = canonicalize(rendered)
    output = rendered.encode()
    atomic_write(root / f"{name}-root.txt", output)
    receipt = dict(
        id=f"{name}-root",
        status="ok",
        sha256=hashlib.sha256(output).hexdigest(),
        normalization_version=normalized["normalization_version"],
        original_raw_sha256=digest,
        original_receipt=evidence["original_receipt"],
        capture_kind="explicit_terminal_rendering",
        rendering_rule=rule,
        split=None,
    )
    atomic_write(
        root / f"{name}-root.receipt.json", (json.dumps(receipt, indent=2) + "\n").encode()
    )
