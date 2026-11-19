"""Canonical text, evidence fields, and catalog validation."""

import hashlib
import json
import re
from importlib.resources import files

from jsonschema import Draft202012Validator

VERSION = "1.0"
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")
LABELS = (
    "usage",
    "section_heading",
    "option_declaration",
    "option_continuation",
    "description_continuation",
    "subcommand_declaration",
    "positional_declaration",
    "prose",
    "blank",
    "other",
)


def canonicalize(text):
    if not isinstance(text, str):
        raise ValueError("input must be UTF-8 text")
    try:
        raw = text.encode("utf-8")
    except UnicodeError as exc:
        raise ValueError("invalid UTF-8 text") from exc
    if len(raw) > 1048576:
        raise ValueError("input exceeds 1 MiB")
    canonical = ANSI.sub("", text.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n"))
    if any((ord(c) < 32 and c not in "\n\t") or 127 <= ord(c) <= 159 for c in canonical):
        raise ValueError("unsupported terminal control")
    lines = canonical.split("\n")
    if len(lines) > 10000 or any(len(line) > 4096 for line in lines):
        raise ValueError("line count or line length limit exceeded")
    return {
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "canonical_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "canonical_text": canonical,
        "normalization_version": VERSION,
        "capture_metadata": {},
    }


def field(lines, spans, *, value=None, rule="identity"):
    evidence = [{"line": line, "start": start, "end": end} for line, start, end in spans]
    literal = "\n".join(lines[line - 1][start:end] for line, start, end in spans)
    return {
        "value": literal if value is None else value,
        "literal": literal,
        "evidence": evidence,
        "rule": rule,
        "provenance": "direct" if rule == "identity" else "deterministic_inference",
    }


def validate_catalog(catalog):
    schema = json.loads(files("helpcat").joinpath("schemas/catalog-1.0.json").read_text())
    Draft202012Validator(schema).validate(catalog)
    lines = catalog["source"]["canonical_text"].split("\n")

    def visit(obj):
        if isinstance(obj, dict):
            if "literal" in obj:
                chunks = []
                for s in obj["evidence"]:
                    if not 1 <= s["line"] <= len(lines):
                        raise ValueError("evidence line out of bounds")
                    line = lines[s["line"] - 1]
                    if not 0 <= s["start"] < s["end"] <= len(line):
                        raise ValueError("evidence column out of bounds")
                    chunks.append(line[s["start"] : s["end"]])
                if "\n".join(chunks) != obj["literal"]:
                    raise ValueError("evidence literal mismatch")
            for v in obj.values():
                visit(v)
        elif isinstance(obj, list):
            for v in obj:
                visit(v)

    visit(catalog)
    identities = [a["value"] for f in catalog["flags"] for a in f["aliases"]]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate flag identity in command scope")
    for flag in catalog["flags"]:
        arity = flag["arity"]["value"] if flag["arity"] else "unknown"
        expected = {"none": False, "required": True, "optional": True, "unknown": None}[arity]
        if flag["takes_value"] != expected:
            raise ValueError("takes_value conflicts with arity")
    return catalog
