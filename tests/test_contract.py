import copy
import hashlib

import pytest
from hypothesis import given, strategies as st

from helpcat import ParserEngine, parse_help, validate_catalog
from helpcat.core import canonicalize


def parse(text):
    return parse_help(text, command_path=("demo", "child"), engine=ParserEngine())


def test_canonicalization_keeps_raw_hash_tabs_and_unicode():
    text = "\ufeffUsage: démo\r\nOptions:\r\n\x1b[32m\t--name NAME\tNom café\x1b[0m\r"
    cat = parse(text)
    assert cat["source"]["raw_sha256"] == hashlib.sha256(text.encode()).hexdigest()
    assert cat["source"]["canonical_text"] == "Usage: démo\nOptions:\n\t--name NAME\tNom café\n"
    assert cat["flags"][0]["description"]["value"] == "Nom café"
    validate_catalog(cat)


@pytest.mark.parametrize(
    "text", ["\x1bX", "\x00", "\x7f", "\ud800", "x" * 1048577, "x" * 4097, "\n" * 10000]
)
def test_invalid_input_fails_without_records(text):
    cat = parse(text)
    assert cat["status"] == "failed"
    assert not cat["flags"]
    assert cat["diagnostics"]
    validate_catalog(cat)


def test_prose_and_examples_do_not_create_flags():
    cat = parse("Usage: demo\nExamples:\n  --fake text  is an example\nProse mentions --other.\n")
    assert not cat["flags"]
    assert cat["status"] == "partial"


def test_repeated_options_conflict_and_scope():
    cat = parse("Options:\n  -v  First\nGlobal options:\n  -v  First\n")
    assert len(cat["flags"]) == 1
    assert cat["status"] == "ok"
    conflict = parse("Options:\n  -v  First\n  -v  Second\n")
    assert conflict["status"] == "partial"
    assert len(conflict["flags"]) == 1
    assert cat["command_path"] == ["demo", "child"]


def test_advertised_entries_no_invented_hierarchy():
    cat = parse("Usage: demo\nCommands:\n  build  Build files\nArguments:\n  FILE  Source file\n")
    assert cat["subcommands"][0]["name"]["value"] == "build"
    assert cat["positionals"][0]["name"]["value"] == "FILE"


def test_span_tampering_is_rejected():
    cat = parse("Options:\n  -v  Details\n")
    bad = copy.deepcopy(cat)
    bad["flags"][0]["aliases"][0]["evidence"][0]["end"] = 100
    with pytest.raises(ValueError, match="bounds"):
        validate_catalog(bad)


def test_real_tagger_handoff_and_abstention():
    class Reference:
        name = "reference"

        def predict(self, lines):
            return [("section_heading", 1), ("option_declaration", 0.2)]

    cat = parse_help(
        "Options:\n  -x  Detail",
        command_path=("x",),
        engine=ParserEngine(tagger=Reference(), threshold=0.9),
    )
    assert cat["status"] == "partial"
    assert cat["flags"] == []


@given(st.text(alphabet=st.characters(blacklist_categories=("Cs", "Cc")), max_size=100))
def test_canonicalization_idempotent(text):
    try:
        once = canonicalize(text)["canonical_text"]
    except ValueError:
        return
    assert canonicalize(once)["canonical_text"] == once


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=30))
def test_evidence_and_duplicate_invariants(name):
    text = f"Options:\n  --{name}  Unicode café\n"
    cat = parse(text)
    validate_catalog(cat)
    assert parse(text) == cat
    assert len(parse(text + text)["flags"]) == 1


def test_repeated_alias_inside_declaration_abstains():
    cat = parse("Options:\n  -v, -v  Details\n")
    assert cat["status"] == "partial"
    assert not cat["flags"]


def test_wrapped_alias_does_not_cross_heading():
    cat = parse("Options:\n  -o,\nOther options:\n  --help  Help\n")
    assert cat["status"] == "partial"
    assert [a["value"] for a in cat["flags"][0]["aliases"]] == ["--help"]
