from copy import deepcopy

from helpcat import ParserEngine, parse_help
from helpcat.audit import audit_catalog


def test_substring_is_not_evidence_for_separately_advertised_alias():
    cat = parse_help(
        "Options:\n  --quiet, -q  Less output", command_path=("demo",), engine=ParserEngine()
    )
    assert audit_catalog(cat) == []
    bad = deepcopy(cat)
    bad["flags"][0]["aliases"][1]["evidence"][0].update(start=3, end=5)
    issues = audit_catalog(bad)
    assert any(i["code"] == "alias_token_boundary" for i in issues)
    assert bad["flags"][0]["aliases"][1]["evidence"][0]["start"] == 3


def test_reference_audit_checks_transformations():
    cat = parse_help(
        "Options:\n  -v  More\n      output", command_path=("demo",), engine=ParserEngine()
    )
    bad = deepcopy(cat)
    bad["flags"][0]["description"]["value"] = "More  output"
    assert any(i["code"] == "transformation" for i in audit_catalog(bad))
