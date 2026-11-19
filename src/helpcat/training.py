"""Atomic resumable CPU checkpoints. Research runs are gated by the CLI."""

import os
from pathlib import Path
import random
import tempfile

import torch

from .core import LABELS
from .features import FEATURE_CONFIG


def save_checkpoint(path, model, optimizer, session):
    required = {"seed", "step", "elapsed_seconds", "code_revision"}
    if not required <= session.keys():
        raise ValueError("checkpoint session is incomplete")
    payload = {
        "version": 1,
        "model_config": model.config,
        "feature_config": FEATURE_CONFIG,
        "labels": list(LABELS),
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "session": dict(session),
        "python_rng": random.getstate(),
        "torch_rng": torch.get_rng_state(),
        "torch_version": str(torch.__version__),
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            torch.save(payload, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def restore_checkpoint(path, model, optimizer=None, *, expected_revision=None):
    payload = torch.load(path, map_location="cpu", weights_only=True)
    if (
        payload["version"] != 1
        or payload["model_config"] != model.config
        or payload["feature_config"] != FEATURE_CONFIG
        or payload["labels"] != list(LABELS)
        or payload["torch_version"] != str(torch.__version__)
    ):
        raise ValueError("checkpoint configuration mismatch")
    if expected_revision is not None and payload["session"]["code_revision"] != expected_revision:
        raise ValueError("checkpoint code revision mismatch")
    model.load_state_dict(payload["model"])
    if optimizer is not None:
        optimizer.load_state_dict(payload["optimizer"])
        random.setstate(payload["python_rng"])
        torch.set_rng_state(payload["torch_rng"])
    return payload["session"]
