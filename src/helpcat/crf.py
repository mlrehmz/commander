"""Experimental CPU CRF; import only when selected."""

import re

from .core import LABELS


def features(lines):
    rows = []
    for i, line in enumerate(lines):
        expanded = line.expandtabs(8)
        row = {
            "bias": 1.0,
            "indent": len(expanded) - len(expanded.lstrip()),
            "length": len(line),
            "blank": not line.strip(),
            "flag": bool(re.match(r"^\s+-[\w-]", line)),
            "heading": line.rstrip().endswith(":"),
            "usage": line.lower().strip().startswith("usage:"),
            "gap": bool(re.search(r"\S {2,}\S", line)),
            "upper": bool(re.search(r"\b[A-Z][A-Z0-9_]+\b", line)),
            "bracket": "[" in line or "<" in line,
        }
        for offset in (-1, 1):
            if 0 <= i + offset < len(lines):
                neighbor = lines[i + offset]
                row[f"{offset}:flag"] = neighbor.lstrip().startswith("-")
                row[f"{offset}:blank"] = not neighbor.strip()
                row[f"{offset}:heading"] = neighbor.rstrip().endswith(":")
        rows.append(row)
    return rows


class CRFTagger:
    name = "crf"

    def __init__(self, path):
        import pycrfsuite

        self.model = pycrfsuite.Tagger()
        self.model.open(str(path))

    def predict(self, lines):
        self.model.set(features(lines))
        labels = self.model.tag()
        if any(label not in LABELS for label in labels):
            raise ValueError("model label vocabulary mismatch")
        return [(label, self.model.marginal(label, i)) for i, label in enumerate(labels)]


def train_crf(pages, path):
    import os
    import tempfile
    from pathlib import Path
    import pycrfsuite

    trainer = pycrfsuite.Trainer(verbose=False)
    for lines, labels in pages:
        if len(lines) != len(labels) or any(label not in LABELS for label in labels):
            raise ValueError("invalid CRF training labels")
        trainer.append(features(lines), labels)
    trainer.set_params(
        {"c1": 0.1, "c2": 0.1, "max_iterations": 100, "feature.possible_transitions": True}
    )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    os.close(fd)
    try:
        trainer.train(temporary)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
