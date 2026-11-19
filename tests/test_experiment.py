import json

import pytest

from helpcat import ParserEngine, parse_help
from helpcat.corpus import load_manifest, require_full_corpus
from helpcat.experiment import assembler_gate, flag_counts, main


def test_empty_corpus_never_passes_gate():
    assert not assembler_gate([])["passed"]
    with pytest.raises(ValueError, match="requires 36"):
        require_full_corpus({"entries": []})
    assert main(["final"]) == 1


def test_counts_use_exact_scope_and_spelling():
    a = parse_help(
        "Options:\n  -v, --verbose  Details", command_path=("demo",), engine=ParserEngine()
    )
    b = parse_help("Options:\n  -v  Details", command_path=("demo",), engine=ParserEngine())
    assert flag_counts(a, b) == {"tp": 1, "fp": 1, "fn": 0}
    b["command_path"] = ["other"]
    assert flag_counts(a, b) == {"tp": 0, "fp": 2, "fn": 1}


def test_metadata_leakage_detected_without_opening_test_files(tmp_path):
    manifest = tmp_path / "manifest.json"
    base = dict(
        id="a",
        project="project",
        leakage_group="group",
        family="unknown",
        split="familiar_test",
        input="missing",
        annotation="missing",
        raw_sha256="a" * 64,
        command_path=["demo"],
        tool_version="1",
        source_url="url",
        license_evidence="url",
        locale=None,
        terminal_width=None,
        synthetic=False,
    )
    other = dict(base, id="b", split="train")
    manifest.write_text(json.dumps({"version": 1, "entries": [base, other]}))
    with pytest.raises(ValueError, match="split leakage"):
        load_manifest(manifest)
