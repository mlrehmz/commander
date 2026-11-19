import pytest

from helpcat.annotation import annotation_packet, validate_pass, compare_passes


def test_packet_has_no_model_predictions_or_reference_guesses():
    packet = annotation_packet(
        "Options:\n  -v  Details\n", ("demo",), annotator="agent-a", producer="agent"
    )
    assert packet["labels"] == [None, None, None]
    assert packet["reference"] is None
    assert packet["source"]["canonical_text"] == "Options:\n  -v  Details\n"
    with pytest.raises(ValueError, match="incomplete"):
        validate_pass(packet)


def test_blind_comparison_requires_matching_source_and_distinct_identity():
    from helpcat import ParserEngine, parse_help

    # This fixture supplies a catalog only to check the review handoff.
    # Production annotation packets contain no predictions.
    text = "Options:\n  -v  Details"
    a = annotation_packet(text, ("demo",), annotator="agent-a", producer="agent")
    a.update(
        labels=["section_heading", "option_declaration"],
        reference=parse_help(text, command_path=("demo",), engine=ParserEngine()),
    )
    b = dict(a, annotator="agent-b", blind=True)
    assert compare_passes(a, b)["disagreements"] == []
    b = dict(b, labels=["prose", "option_declaration"])
    assert compare_passes(a, b)["disagreements"][0]["kind"] == "line_label"
    with pytest.raises(ValueError, match="distinct"):
        compare_passes(a, dict(b, annotator="agent-a"))
