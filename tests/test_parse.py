from helpcat import ParserEngine, parse_help


def test_aliases_keep_source_evidence():
    cat = parse_help(
        "Usage: demo [OPTIONS]\nOptions:\n  -v, --verbose  Show details\n",
        command_path=("demo",),
        engine=ParserEngine(),
    )
    assert cat["status"] == "ok"
    flag = cat["flags"][0]
    assert [a["value"] for a in flag["aliases"]] == ["-v", "--verbose"]
    assert flag["description"]["value"] == "Show details"
    for alias in flag["aliases"]:
        span = alias["evidence"][0]
        assert (
            cat["source"]["canonical_text"].splitlines()[span["line"] - 1][
                span["start"] : span["end"]
            ]
            == alias["literal"]
        )


def test_notations_and_wrapped_description():
    text = (
        "Usage: demo\nOptions:\n"
        "  --color[=WHEN]  Color mode\n"
        "                  across lines\n"
        "  --[no-]foo      Toggle foo\n"
        "  -I<dir>         Include directory\n"
    )
    cat = parse_help(text, command_path=("demo",), engine=ParserEngine())
    assert [f["takes_value"] for f in cat["flags"]] == [True, None, True]
    assert cat["flags"][0]["arity"]["value"] == "optional"
    assert cat["flags"][0]["description"]["value"] == "Color mode across lines"
    assert len(cat["flags"][0]["description"]["evidence"]) == 2
    assert [a["value"] for a in cat["flags"][1]["aliases"]] == ["--foo", "--no-foo"]


def test_wrapped_alias_declaration_is_one_record():
    cat = parse_help(
        "Options:\n  -o,\n  --output FILE  Write output\n",
        command_path=("demo",),
        engine=ParserEngine(),
    )
    assert len(cat["flags"]) == 1
    assert [a["value"] for a in cat["flags"][0]["aliases"]] == ["-o", "--output"]
    assert cat["flags"][0]["arity"]["value"] == "required"
