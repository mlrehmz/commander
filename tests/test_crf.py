import pytest

from helpcat import ParserEngine, parse_help


def test_real_crf_handoff(tmp_path):
    pytest.importorskip("pycrfsuite")
    from helpcat.crf import CRFTagger, train_crf

    lines = ["Options:", "  -v, --verbose  Details"]
    labels = ["section_heading", "option_declaration"]
    model = tmp_path / "tiny.crf"
    train_crf([(lines, labels)] * 5, model)
    cat = parse_help(
        "\n".join(lines), command_path=("demo",), engine=ParserEngine(tagger=CRFTagger(model))
    )
    assert [a["value"] for a in cat["flags"][0]["aliases"]] == ["-v", "--verbose"]
