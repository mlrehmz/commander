"""Lazy tagger loading; runtime rules need no training libraries."""

import json
from pathlib import Path

from .parser import ParserEngine, RulesTagger


def load_engine(name="rules", *, model=None, policy=None):
    if name == "rules":
        tagger = RulesTagger()
    elif name == "crf":
        from .crf import CRFTagger

        if model is None:
            raise ValueError("CRF requires --model")
        tagger = CRFTagger(model)
    else:
        raise ValueError(f"unknown engine: {name}")
    config = json.loads(Path(policy).read_text()) if policy else {}
    if config.get("engine", name) != name:
        raise ValueError("policy engine mismatch")
    if name != "rules" and not policy:
        raise ValueError("learned engines require a record-selection policy")
    if config.get("calibrated"):
        raise ValueError(
            "calibrated policy artifacts are not yet supported; use experimental policy"
        )
    return ParserEngine(
        tagger=tagger,
        threshold=config.get("threshold", 0.0),
        version=config.get("version", f"{name}-1"),
        calibrated=False,
    )
