"""Source-reference checks beyond JSON shape and substring fidelity."""

import re

from .core import validate_catalog


def audit_catalog(catalog):
    validate_catalog(catalog)
    lines = catalog["source"]["canonical_text"].split("\n")
    issues = []

    def issue(path, code, message):
        issues.append({"path": path, "code": code, "message": message})

    def visit(value, path):
        if isinstance(value, dict):
            if "literal" in value:
                rule = value["rule"]
                literal = value["literal"]
                normalized = value["value"]
                expected = None
                if rule == "identity":
                    expected = literal
                elif rule == "join-description-whitespace":
                    expected = " ".join(literal.split())
                elif rule == "expand-negatable":
                    match = re.fullmatch(r"--\[no-\]([\w-]+)", literal)
                    if not match or normalized not in ("--" + match[1], "--no-" + match[1]):
                        issue(
                            path, "transformation", "Expanded alias does not match source notation."
                        )
                elif rule == "declaration-value-notation":
                    if normalized not in ("none", "required", "optional", "unknown"):
                        issue(path, "transformation", "Invalid arity interpretation.")
                if expected is not None and normalized != expected:
                    issue(
                        path,
                        "transformation",
                        "Normalized value does not match the documented rule.",
                    )
                provenance = "direct" if rule == "identity" else "deterministic_inference"
                if value["provenance"] != provenance:
                    issue(path, "provenance", "Provenance does not match transformation rule.")
            for key, child in value.items():
                visit(child, path + "/" + key)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, path + "/" + str(index))

    visit(catalog, "")
    for i, flag in enumerate(catalog["flags"]):
        for j, alias in enumerate(flag["aliases"]):
            path = f"/flags/{i}/aliases/{j}"
            if len(alias["evidence"]) != 1:
                issue(path, "alias_token_boundary", "Alias evidence must be one declaration token.")
                continue
            span = alias["evidence"][0]
            line = lines[span["line"] - 1]
            before = line[span["start"] - 1] if span["start"] else ""
            after = line[span["end"] : span["end"] + 1]
            attached = False
            meta = flag["metavar"]
            if meta and flag["arity"] and flag["arity"]["value"] == "required":
                attached = any(
                    s["line"] == span["line"] and s["start"] == span["end"]
                    for s in meta["evidence"]
                )
            if (before and re.match(r"[\w-]", before)) or (
                after and re.match(r"[\w-]", after) and not attached
            ):
                issue(
                    path,
                    "alias_token_boundary",
                    "Span selects part of another token, not an advertised alias.",
                )
    return issues
