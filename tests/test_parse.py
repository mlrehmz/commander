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


def test_lowercase_and_optional_metavars_from_pilot_layouts():
    cat = parse_help(
        "Options:\n  -p path, --python path  Interpreter\n"
        "  --provision [CONFIG]  Optional configuration\n"
        "  --search d [d ...]  Search locations\n",
        command_path=("demo",),
        engine=ParserEngine(),
    )
    assert len(cat["flags"]) == 3
    assert [a["value"] for a in cat["flags"][0]["aliases"]] == ["-p", "--python"]
    assert cat["flags"][0]["metavar"]["value"] == "path"
    assert cat["flags"][1]["arity"]["value"] == "optional"
    assert cat["flags"][2]["metavar"]["value"] == "d [d ...]"


def test_unsupported_boxed_option_omission_is_detected():
    cat = parse_help(
        "Usage: demo\n╭─ Options ─╮\n│ --@unknown   Detail │\n╰───────────╯",
        command_path=("demo",),
        engine=ParserEngine(),
    )
    assert cat["status"] == "partial"
    assert cat["diagnostics"]


def test_generic_boxed_rows_keep_alias_groups_and_exact_description_spans():
    from helpcat.audit import audit_catalog

    text = (
        "Usage: demo\n╭─ Options ─╮\n"
        "│ -n  --name NAME   Display name │\n"
        "│                   across lines │\n╰───────────╯"
    )
    cat = parse_help(text, command_path=("demo",), engine=ParserEngine())
    assert [a["value"] for a in cat["flags"][0]["aliases"]] == ["-n", "--name"]
    assert cat["flags"][0]["description"]["value"] == "Display name across lines"
    assert cat["flags"][0]["metavar"]["value"] == "NAME"
    assert audit_catalog(cat) == []


def test_compound_metavars_and_bracket_choices_keep_semantic_uncertainty():
    text = (
        "Options:\n  --auth USER[:PASS] | TOKEN, -a USER[:PASS] | TOKEN\n"
        "      Credentials\n  --proxy PROTOCOL:ADDRESS  Proxy\n"
        "  --jobs INTEGER RANGE  Workers\n  --color [red|blue]  Color\n"
    )
    cat = parse_help(text, command_path=("demo",), engine=ParserEngine())
    assert len(cat["flags"]) == 4
    assert [a["value"] for a in cat["flags"][0]["aliases"]] == ["--auth", "-a"]
    assert [f["metavar"]["value"] for f in cat["flags"]] == [
        "USER[:PASS] | TOKEN",
        "PROTOCOL:ADDRESS",
        "INTEGER RANGE",
        "[red|blue]",
    ]
    assert cat["flags"][3]["arity"] is None
    assert cat["flags"][3]["takes_value"] is None


def test_advertised_aliases_and_standalone_positionals_share_wrapped_evidence():
    text = (
        "Usage: demo\nArguments:\n  INPUT\n      Source file\n\n"
        "Commands:\n  build (b)   Build output\n              across lines\n"
    )
    cat = parse_help(text, command_path=("demo",), engine=ParserEngine())
    assert cat["positionals"][0]["name"]["value"] == "INPUT"
    assert cat["positionals"][0]["description"]["value"] == "Source file"
    assert [c["name"]["value"] for c in cat["subcommands"]] == ["build", "b"]
    assert [c["description"]["value"] for c in cat["subcommands"]] == [
        "Build output across lines"
    ] * 2


def test_description_paragraphs_can_quote_flags_without_creating_declarations():
    text = (
        "Options:\n  --format TEXT\n      Format options:\n\n"
        "          --example=value\n\n      More details\n  --help  Help\n"
    )
    cat = parse_help(text, command_path=("demo",), engine=ParserEngine())
    assert [a["value"] for f in cat["flags"] for a in f["aliases"]] == ["--format", "--help"]
    assert cat["flags"][0]["description"]["value"] == "Format options: --example=value More details"


def test_direct_literal_defaults_and_choices_preserve_uncertainty_and_evidence():
    from helpcat.audit import audit_catalog

    text = (
        "Options:\n  --mode {fast,slow}  Mode (default: fast)\n"
        "  --count INTEGER  Count [default: 8]\n"
        "  --config FILE  Config (default: None)\n"
        "  --maybe [CONFIG]  Optional value\n"
        "  --color [red|blue]  Color\n"
    )
    cat = parse_help(text, command_path=("demo",), engine=ParserEngine())
    assert cat["flags"][0]["choices"]["value"] == "fast,slow"
    assert cat["flags"][0]["default"]["value"] == "fast"
    assert cat["flags"][1]["default"]["value"] == "8"
    assert cat["flags"][2]["default"]["value"] == "None"
    assert cat["flags"][2]["default"]["provenance"] == "direct"
    assert cat["flags"][3]["choices"] is None
    assert cat["flags"][4]["choices"]["value"] == "red|blue"
    assert cat["flags"][4]["arity"] is None
    assert audit_catalog(cat) == []


def test_unseparated_short_clusters_are_not_guessed_as_attached_metavars():
    cat = parse_help(
        "Options:\n  -longname  Unknown notation\n  -I<dir>  Include\n",
        command_path=("demo",),
        engine=ParserEngine(),
    )
    assert [a["value"] for f in cat["flags"] for a in f["aliases"]] == ["-I"]
    assert cat["status"] == "partial"
