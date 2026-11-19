"""Versioned line features; canonical source text is never truncated."""

import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile

FEATURE_CONFIG = {
    "version": "features-1",
    "normalization_version": "1.0",
    "byte_width": 48,
    "tab_width": 8,
}
NUMERIC_WIDTH = 10


def windows(length, *, size=256, overlap=32):
    if length < 0 or not 0 <= overlap < size:
        raise ValueError("invalid window geometry")
    return [(start, min(length, start + size)) for start in range(0, length, size - overlap)]


def merge_predictions(length, predictions):
    chosen = [None] * length
    context = [-1] * length
    for start, rows in sorted(predictions, key=lambda p: p[0]):
        if start < 0 or start + len(rows) > length:
            raise ValueError("window outside page")
        for offset, row in enumerate(rows):
            score = min(offset, len(rows) - offset - 1)
            if score > context[start + offset]:
                chosen[start + offset], context[start + offset] = row, score
    if any(row is None for row in chosen):
        raise ValueError("window predictions do not cover page")
    return chosen


def payload_digest(features):
    return hashlib.sha256(
        json.dumps(
            {key: features[key] for key in ("bytes", "numeric")},
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def extract_features(text, config=None):
    config = dict(FEATURE_CONFIG if config is None else config)
    if config["version"] != "features-1" or config["normalization_version"] != "1.0":
        raise ValueError("unsupported feature version")
    if not 1 <= config["byte_width"] <= 4096 or config["tab_width"] <= 0:
        raise ValueError("invalid feature dimensions")
    encoded = []
    numeric = []
    for line in text.split("\n"):
        raw = list(line.encode("utf-8")[: config["byte_width"]])
        encoded.append([b + 1 for b in raw] + [0] * (config["byte_width"] - len(raw)))
        expanded = line.expandtabs(config["tab_width"])
        stripped = line.strip()
        numeric.append(
            [
                math.log1p(len(expanded) - len(expanded.lstrip())) / 8,
                math.log1p(len(line)) / 8,
                float(not stripped),
                float(stripped.startswith("-")),
                float(stripped.endswith(":")),
                float(stripped.lower().startswith("usage:")),
                float(bool(re.search(r"\S {2,}\S", line))),
                float(bool(re.search(r"\b[A-Z][A-Z0-9_]+\b", line))),
                float("[" in line or "<" in line),
                float("\t" in line),
            ]
        )
    digest = hashlib.sha256(text.encode()).hexdigest()
    key = hashlib.sha256(
        json.dumps({"source": digest, "config": config}, sort_keys=True).encode()
    ).hexdigest()
    result = {
        "key": key,
        "source_sha256": digest,
        "config": config,
        "bytes": encoded,
        "numeric": numeric,
    }
    result["payload_sha256"] = payload_digest(result)
    return result


class FeatureCache:
    def __init__(self, folder):
        self.folder = Path(folder)

    def get(self, text, config=None):
        config = dict(FEATURE_CONFIG if config is None else config)
        digest = hashlib.sha256(text.encode()).hexdigest()
        key = hashlib.sha256(
            json.dumps({"source": digest, "config": config}, sort_keys=True).encode()
        ).hexdigest()
        path = self.folder / (key + ".json")
        if path.exists():
            try:
                cached = json.loads(path.read_text())
                expected_lines = len(text.split("\n"))
                if (
                    cached["key"] == key
                    and cached["source_sha256"] == digest
                    and cached["config"] == config
                    and cached["payload_sha256"] == payload_digest(cached)
                    and len(cached["bytes"]) == expected_lines
                    and len(cached["numeric"]) == expected_lines
                    and all(len(r) == config["byte_width"] for r in cached["bytes"])
                    and all(len(r) == NUMERIC_WIDTH for r in cached["numeric"])
                ):
                    return cached
            except (ValueError, KeyError, TypeError):
                pass
        features = extract_features(text, config)
        self.folder.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=self.folder)
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump(features, stream, separators=(",", ":"))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return features
