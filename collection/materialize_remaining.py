"""Source-only primary transcriptions for the remaining eight pilot pages.

The line numbers, names and ranges below were reviewed against raw captures.
This script selects those spans. It never imports or runs a parser or tagger.
"""

import json
from pathlib import Path
import re

from helpcat.annotation import annotation_packet, validate_pass
from helpcat.collect import atomic_write
from helpcat.core import field


def R(first, last=None):
    return list(range(first, (first if last is None else last) + 1))


def F(line, names, meta=None, description=None, arity=None):
    return {
        "line": line,
        "names": names.split(),
        "meta": meta,
        "description": description or [],
        "arity": arity if arity else ("required" if meta else None),
    }


PAGES = {
    "black-root": {
        "command": ["black"],
        "usage": [1],
        "headings": [5],
        "flags": [
            F(6, "-c --code", "TEXT", R(6)),
            F(7, "-l --line-length", "INTEGER", R(7, 8)),
            F(
                9,
                "-t --target-version",
                "[py33|py34|py35|py36|py37|py38|py39|py310|py311|py312|py313|py314]",
                R(10, 16),
                "unknown",
            ),
            F(17, "--pyi", description=R(17, 19)),
            F(20, "--ipynb", description=R(20, 23)),
            F(24, "--python-cell-magics", "TEXT", R(24, 28)),
            F(29, "-x --skip-source-first-line", description=R(29)),
            F(30, "-S --skip-string-normalization", description=R(31)),
            F(32, "-C --skip-magic-trailing-comma", description=R(33, 34)),
            F(35, "--preview", description=R(35, 37)),
            F(38, "--unstable", description=R(38, 42)),
            F(
                43,
                "--enable-unstable-feature",
                "[string_processing|hug_parens_with_braces_and_square_brackets|wrap_long_dict_values_in_parens|multiline_string_handling|always_one_newline_after_import|fix_fmt_skip_in_one_liners|wrap_comprehension_in|remove_parens_around_except_types|normalize_cr_newlines]",
                R(44, 48),
                "unknown",
            ),
            F(49, "--check", description=R(49, 53)),
            F(54, "--diff", description=R(54, 57)),
            F(58, "--color --no-color", description=R(58, 59)),
            F(60, "--line-ranges", "START-END", R(60, 67)),
            F(68, "--fast --safe", description=R(68, 72)),
            F(73, "--required-version", "TEXT", R(73, 80)),
            F(81, "--exclude", "TEXT", R(81, 93)),
            F(94, "--extend-exclude", "TEXT", R(94, 96)),
            F(97, "--force-exclude", "TEXT", R(97, 103)),
            F(104, "--stdin-filename", "TEXT", R(104, 107)),
            F(108, "--include", "TEXT", R(108, 116)),
            F(117, "-W --workers", "INTEGER RANGE", R(117, 123)),
            F(124, "-q --quiet", description=R(124, 126)),
            F(127, "-v --verbose", description=R(127, 131)),
            F(132, "--version", description=R(132)),
            F(133, "--config", "FILE", R(133, 134)),
            F(135, "-h --help", description=R(135)),
        ],
        "notes": [
            "Bracketed pipe-separated choices do not establish optional value arity without formatter knowledge; arity remains unknown.",
            "Usage SRC is not a separate positional declaration.",
        ],
    },
    "pipx-root": {
        "command": ["pipx"],
        "usage": R(1, 3),
        "headings": [14, 32, 43],
        "other": [46],
        "flags": [
            F(33, "-h --help", description=R(33)),
            F(34, "--quiet -q", description=R(34, 36)),
            F(37, "--verbose -v", description=R(37, 39)),
            F(40, "--global", description=R(40)),
            F(41, "--version", description=R(41)),
        ],
        "commands": [
            (47, "install", R(47)),
            (48, "install-all", R(48)),
            (49, "uninject", R(49, 50)),
            (51, "inject", R(51)),
            (52, "pin", R(52, 53)),
            (54, "unpin", R(54)),
            (55, "upgrade", R(55)),
            (56, "upgrade-all", R(56, 57)),
            (58, "upgrade-shared", R(58)),
            (59, "uninstall", R(59)),
            (60, "uninstall-all", R(60)),
            (61, "reinstall", R(61)),
            (62, "reinstall-all", R(62)),
            (63, "list", R(63)),
            (64, "interpreter", R(64)),
            (65, "run", R(65, 68)),
            (69, "runpip", R(69, 70)),
            (71, "ensurepath", R(71, 72)),
            (73, "environment", R(73, 74)),
            (75, "completions", R(75, 76)),
        ],
        "notes": [
            "Environment variables are prose, not positionals or flags. The brace command summary duplicates the explicitly advertised rows."
        ],
    },
    "pipenv-root": {
        "command": ["pipenv"],
        "usage": [1],
        "headings": [3, 26, 51],
        "other": [28, 31, 34, 37, 40, 43, 46, 49],
        "flags": [
            F(4, "--where", description=R(4)),
            F(5, "--venv", description=R(5)),
            F(6, "--py", description=R(6)),
            F(7, "--envs", description=R(7)),
            F(8, "--rm", description=R(8)),
            F(9, "--bare", description=R(9)),
            F(10, "--man", description=R(10)),
            F(11, "--support", description=R(11, 12)),
            F(13, "--site-packages --no-site-packages", description=R(14)),
            F(16, "--python", "TEXT", R(16, 17)),
            F(18, "--clear", description=R(18)),
            F(19, "-q --quiet", description=R(19)),
            F(20, "-v --verbose", description=R(20)),
            F(21, "--pypi-mirror", "TEXT", R(21)),
            F(22, "--version", description=R(22)),
            F(23, "-h --help", description=R(23)),
        ],
        "commands": [
            (52, "check", R(52, 53)),
            (54, "clean", R(54)),
            (55, "graph", R(55)),
            (56, "install", R(56, 57)),
            (58, "lock", R(58)),
            (59, "open", R(59)),
            (60, "requirements", R(60)),
            (61, "run", R(61)),
            (62, "scripts", R(62)),
            (63, "shell", R(63)),
            (64, "sync", R(64)),
            (65, "uninstall", R(65)),
            (66, "update", R(66)),
            (67, "upgrade", R(67, 68)),
            (69, "verify", R(69)),
        ],
    },
    "tox-root": {
        "command": ["tox"],
        "usage": R(2, 4),
        "headings": [8, 26, 32],
        "other": [35],
        "flags": [
            F(9, "-h --help", description=R(9)),
            F(10, "--colored", "{yes,no}", R(10)),
            F(
                11,
                "--stderr-color",
                "{BLACK,BLUE,CYAN,GREEN,LIGHTBLACK_EX,LIGHTBLUE_EX,LIGHTCYAN_EX,LIGHTGREEN_EX,LIGHTMAGENTA_EX,LIGHTRED_EX,LIGHTWHITE_EX,LIGHTYELLOW_EX,MAGENTA,RED,RESET,WHITE,YELLOW}",
                R(12),
            ),
            F(13, "--exit-and-dump-after", "seconds", R(14)),
            F(15, "-c --conf", "file", R(15)),
            F(16, "--workdir", "dir", R(16)),
            F(17, "--root", "dir", R(17)),
            F(18, "--runner", "{virtualenv}", R(18)),
            F(19, "--version", description=R(19)),
            F(20, "--no-provision", "[REQ_JSON]", R(20), "optional"),
            F(21, "--no-recreate-provision", description=R(21)),
            F(22, "-r --recreate", description=R(22)),
            F(23, "-x --override", "OVERRIDE", R(24)),
            F(29, "-v --verbose", description=R(29)),
            F(30, "-q --quiet", description=R(30)),
        ],
        "commands": [
            (36, "run", R(36), "(r)"),
            (36, "r", R(36), "(r)"),
            (37, "run-parallel", R(37), "(p)"),
            (37, "p", R(37), "(p)"),
            (38, "depends", R(38), "(de)"),
            (38, "de", R(38), "(de)"),
            (39, "list", R(39), "(l)"),
            (39, "l", R(39), "(l)"),
            (40, "devenv", R(40), "(d)"),
            (40, "d", R(40), "(d)"),
            (41, "schema", R(41)),
            (42, "config", R(42), "(c)"),
            (42, "c", R(42), "(c)"),
            (43, "quickstart", R(43), "(q)"),
            (43, "q", R(43), "(q)"),
            (44, "exec", R(44), "(e)"),
            (44, "e", R(44), "(e)"),
            (45, "legacy", R(45), "(le)"),
            (45, "le", R(45), "(le)"),
        ],
        "notes": [
            "Parenthesized command aliases are explicitly advertised spellings; v1 schema records them separately, not as inferred hierarchy.",
            "Root/config notices are prose; optional REQ_JSON notation supplies optional value arity.",
        ],
    },
    "virtualenv-root": {
        "command": ["virtualenv"],
        "usage": R(1, 4),
        "headings": [6, 15, 21, 28, 40, 56],
        "flags": [
            F(7, "--version", description=R(7)),
            F(8, "--with-traceback", description=R(8)),
            F(9, "--read-only-app-data", description=R(9)),
            F(10, "--app-data", "APP_DATA", R(10)),
            F(11, "--reset-app-data", description=R(11)),
            F(12, "--upgrade-embed-wheels", description=R(12)),
            F(13, "-h --help", description=R(13)),
            F(18, "-v --verbose", description=R(18)),
            F(19, "-q --quiet", description=R(19)),
            F(24, "--discovery", "{builtin}", R(24)),
            F(25, "-p --python", "py", R(25)),
            F(26, "--try-first-with", "py_exe", R(26)),
            F(31, "--creator", "{builtin,cpython3-posix,venv}", R(32)),
            F(34, "--clear", description=R(34)),
            F(35, "--no-vcs-ignore", description=R(35)),
            F(36, "--system-site-packages", description=R(36)),
            F(37, "--symlinks", description=R(37)),
            F(38, "--copies --always-copy", description=R(38)),
            F(43, "--seeder", "{app-data,pip}", R(43)),
            F(44, "--no-seed --without-pip", description=R(44)),
            F(45, "--no-download --never-download", description=R(46)),
            F(47, "--download", description=R(47)),
            F(48, "--extra-search-dir", "d [d ...]", R(48)),
            F(49, "--pip", "version", R(49)),
            F(50, "--setuptools", "version", R(50)),
            F(51, "--no-pip", description=R(51)),
            F(52, "--no-setuptools", description=R(52)),
            F(53, "--no-periodic-update", description=R(53)),
            F(54, "--symlink-app-data", description=R(54)),
            F(59, "--activators", "comma_sep_list", R(59)),
            F(60, "--prompt", "prompt", R(60)),
        ],
        "positionals": [(33, "dest", R(33))],
    },
    "datasette-root": {
        "command": ["datasette"],
        "usage": [1],
        "headings": [8, 12],
        "flags": [F(9, "--version", description=R(9)), F(10, "--help", description=R(10))],
        "commands": [
            (13, "serve*", R(13)),
            (14, "inspect", R(14)),
            (15, "install", R(15)),
            (16, "package", R(16)),
            (17, "plugins", R(17)),
            (18, "publish", R(18)),
            (19, "uninstall", R(19)),
        ],
        "notes": [
            "The source advertises serve* without a legend. Preserve the literal marker, not an inferred default or normalized invocation.",
            "Printed ellipses are retained; missing description text is not reconstructed.",
        ],
    },
    "rich-cli-root": {
        "command": ["rich"],
        "usage": [5],
        "headings": [7],
        "other": [66],
        "boxed": True,
        "flags": [
            F(8, "-p --print", description=R(8, 9)),
            F(10, "-u --rule", description=R(10)),
            F(11, "-J --json", description=R(11)),
            F(12, "-m --markdown", description=R(12)),
            F(13, "--rst", description=R(13)),
            F(14, "--csv", description=R(14)),
            F(15, "--ipynb", description=R(15)),
            F(16, "--syntax", description=R(16)),
            F(17, "--inspect", description=R(17)),
            F(18, "-h --head", "LINES", R(18, 19)),
            F(20, "-t --tail", "LINES", R(20, 21)),
            F(22, "-j --emoji", description=R(22)),
            F(23, "-l --left", description=R(23)),
            F(24, "-r --right", description=R(24)),
            F(25, "-c --center", description=R(25)),
            F(26, "-L --text-left", description=R(26)),
            F(27, "-R --text-right", description=R(27)),
            F(28, "-C --text-center", description=R(28)),
            F(29, "-F --text-full", description=R(29, 30)),
            F(31, "--soft", description=R(31, 32)),
            F(33, "-e --expand", description=R(33, 34)),
            F(35, "-w --width", "SIZE", R(35)),
            F(36, "-W --max-width", "SIZE", R(36)),
            F(37, "-s --style", "STYLE", R(37)),
            F(38, "--rule-style", "STYLE", R(38)),
            F(39, "--rule-char", "CHARACTER", R(39, 40)),
            F(41, "-d --padding", "TOP,RIGHT,BOTTOM,LEFT", R(41, 42)),
            F(43, "-a --panel", "BOX", R(43, 44)),
            F(45, "-S --panel-style", "STYLE", R(45, 46)),
            F(47, "--theme", "THEME", R(47, 48)),
            F(49, "-n --line-numbers", description=R(49)),
            F(50, "-g --guides", description=R(50, 51)),
            F(52, "-x --lexer", "LEXER", R(52, 53)),
            F(54, "-y --hyperlinks", description=R(54)),
            F(55, "--no-wrap", description=R(55, 56)),
            F(57, "--title", "TEXT", R(57)),
            F(58, "--caption", "TEXT", R(58)),
            F(59, "--force-terminal", description=R(59, 60)),
            F(61, "-o --export-html", "PATH", R(61)),
            F(62, "--export-svg", "PATH", R(62)),
            F(63, "--pager", description=R(63)),
            F(64, "-v --version", description=R(64)),
            F(65, "--help", description=R(65)),
        ],
        "notes": [
            "Box borders/padding are not description text. Preserve printed Unicode truncation and version banner exactly in canonical source.",
            "Positional usage placeholders do not constitute separate declarations.",
        ],
    },
    "httpie-root": {
        "command": ["http"],
        "usage": [1, 2],
        "headings": [6, 68, 103, 113, 182, 255, 275, 295, 340, 378, 406],
        "flags": [
            F(70, "--json -j", description=R(71, 73)),
            F(75, "--form -f", description=R(76, 80)),
            F(82, "--multipart", description=R(83)),
            F(85, "--boundary", "BOUNDARY", R(86)),
            F(88, "--raw", "RAW", R(89, 100)),
            F(105, "--compress -x", description=R(106, 110)),
            F(115, "--pretty", "{all,colors,format,none}", R(116, 118)),
            F(120, "--style -s", "STYLE", R(121, 137)),
            F(139, "--unsorted", description=R(140, 142)),
            F(144, "--sorted", description=R(145, 147)),
            F(149, "--response-charset", "ENCODING", R(150, 153)),
            F(155, "--response-mime", "MIME_TYPE", R(156, 159)),
            F(161, "--format-options", "FORMAT_OPTIONS", R(162, 179)),
            F(184, "--print -p", "WHAT", R(185, 196)),
            F(198, "--headers -h", description=R(199)),
            F(201, "--meta -m", description=R(202)),
            F(204, "--body -b", description=R(205)),
            F(207, "--verbose -v", description=R(208, 214)),
            F(216, "--all", description=R(217, 220)),
            F(222, "--stream -S", description=R(223, 232)),
            F(234, "--output -o", "FILE", R(235, 237)),
            F(239, "--download -d", description=R(240, 242)),
            F(244, "--continue -c", description=R(245, 246)),
            F(248, "--quiet -q", description=R(249, 252)),
            F(257, "--session", "SESSION_NAME_OR_PATH", R(258, 268)),
            F(270, "--session-read-only", "SESSION_NAME_OR_PATH", R(271, 272)),
            F(277, "--auth -a", "USER[:PASS] | TOKEN", R(278, 280)),
            F(282, "--auth-type -A", "{basic,bearer,digest}", R(283, 289)),
            F(291, "--ignore-netrc", description=R(292)),
            F(297, "--offline", description=R(298)),
            F(300, "--proxy", "PROTOCOL:PROXY_URL", R(301, 304)),
            F(306, "--follow -F", description=R(307)),
            F(309, "--max-redirects", "MAX_REDIRECTS", R(310)),
            F(312, "--max-headers", "MAX_HEADERS", R(313)),
            F(315, "--timeout", "SECONDS", R(316, 321)),
            F(323, "--check-status", description=R(324, 331)),
            F(333, "--path-as-is", description=R(334)),
            F(336, "--chunked", description=R(337)),
            F(342, "--verify", "VERIFY", R(343, 346)),
            F(348, "--ssl", "{ssl2.3,tls1,tls1.1,tls1.2}", R(349, 353)),
            F(355, "--ciphers", "CIPHERS", R(356, 361)),
            F(363, "--cert", "CERT", R(364, 366)),
            F(368, "--cert-key", "CERT_KEY", R(369, 370)),
            F(372, "--cert-key-pass", "CERT_KEY_PASS", R(373, 375)),
            F(380, "--ignore-stdin -I", description=R(381)),
            F(383, "--help", description=R(384)),
            F(386, "--manual", description=R(387)),
            F(389, "--version", description=R(390)),
            F(392, "--traceback", description=R(393)),
            F(395, "--default-scheme", "DEFAULT_SCHEME", R(396)),
            F(398, "--debug", description=R(399, 400)),
        ],
        "positionals": [
            (11, "METHOD", R(12, 18)),
            (20, "URL", R(21, 27)),
            (29, "REQUEST_ITEM", R(30, 65)),
        ],
        "notes": [
            "Examples and value lists inside an argument description remain part of that description, not extra declarations.",
            "The generic --no-OPTION prose is not an explicit declaration of concrete aliases and is not expanded.",
            "USER[:PASS] | TOKEN and PROTOCOL:PROXY_URL are source metavars; no authentication/type semantics inferred.",
        ],
    },
}


def bounds(line, boxed):
    start = 1 if boxed and line.startswith("│") else 0
    end = line.rfind("│") if boxed and line.endswith("│") else len(line)
    text = line[start:end]
    return start + len(text) - len(text.lstrip()), start + len(text.rstrip())


def token_span(line, token):
    match = re.search(r"(?<![\w-])" + re.escape(token) + r"(?![\w-])", line)
    if match is None:
        raise ValueError(f"reviewed token not found: {token}")
    return match.start(), match.end()


def materialize(identifier, spec):
    text = Path(f"corpus/intake/{identifier}.txt").read_bytes().decode("utf-8")
    packet = annotation_packet(
        text, tuple(spec["command"]), annotator="codex-primary-2026-11-19", producer="agent"
    )
    lines = packet["source"]["canonical_text"].split("\n")
    boxed = spec.get("boxed", False)
    labels = ["blank" if not line.strip() else "prose" for line in lines]
    for label, key in [("usage", "usage"), ("section_heading", "headings"), ("other", "other")]:
        for n in spec.get(key, []):
            labels[n - 1] = label

    def word(n, value):
        a, b = token_span(lines[n - 1], value)
        return field(lines, [(n, a, b)])

    def description(n, numbers, end):
        spans = []
        for dn in numbers:
            a, b = bounds(lines[dn - 1], boxed)
            if dn == n:
                a = end + len(lines[dn - 1][end:b]) - len(lines[dn - 1][end:b].lstrip())
            if a >= b:
                continue
            spans.append((dn, a, b))
            if dn != n:
                labels[dn - 1] = "description_continuation"
        if not spans:
            return None
        result = field(lines, spans)
        if len(spans) > 1:
            result = field(
                lines,
                spans,
                value=" ".join(result["literal"].split()),
                rule="join-description-whitespace",
            )
        return result

    ref = {
        "schema_version": "1.0",
        "source": packet["source"],
        "command_path": spec["command"],
        "flags": [],
        "subcommands": [],
        "positionals": [],
        "status": "ok",
        "diagnostics": [],
        "engine": {
            "name": "manual-agent-annotation",
            "version": "primary-1",
            "threshold": 0.0,
            "calibrated": False,
        },
    }
    for f in spec["flags"]:
        n = f["line"]
        line = lines[n - 1]
        labels[n - 1] = "option_declaration"
        aliases = [word(n, name) for name in f["names"]]
        end = max(a["evidence"][0]["end"] for a in aliases)
        meta = None
        if f["meta"]:
            start = line.index(f["meta"], end)
            end = start + len(f["meta"])
            meta = field(lines, [(n, start, end)])
        arity = None
        if f["arity"] not in (None, "unknown"):
            arity = field(
                lines, [(n, start, end)], value=f["arity"], rule="declaration-value-notation"
            )
        ref["flags"].append(
            {
                "aliases": aliases,
                "metavar": meta,
                "arity": arity,
                "takes_value": True if arity else None,
                "required_presence": None,
                "type": None,
                "default": None,
                "choices": None,
                "description": description(n, f["description"], end),
                "selection_score": 1.0,
            }
        )
    for kind, key in [("subcommands", "commands"), ("positionals", "positionals")]:
        for row in spec.get(key, []):
            n, name, numbers, *marker = row
            labels[n - 1] = (
                "subcommand_declaration" if kind == "subcommands" else "positional_declaration"
            )
            name_field = word(n, name)
            end = name_field["evidence"][0]["end"]
            if marker:
                end = lines[n - 1].index(marker[0]) + len(marker[0])
            ref[kind].append(
                {
                    "name": name_field,
                    "description": description(n, numbers, end),
                    "selection_score": 1.0,
                }
            )
    packet.update(
        labels=labels,
        reference=ref,
        notes=[
            "Primary agent source pass; no parser/tagger outputs read.",
            *spec.get("notes", []),
            "Optional semantics without a documented supported interpretation stay unknown. Blind comparison pending.",
        ],
    )
    validate_pass(packet)
    return packet


if __name__ == "__main__":
    for identifier, spec in PAGES.items():
        packet = materialize(identifier, spec)
        atomic_write(
            f"corpus/annotations/primary/{identifier}.json",
            (json.dumps(packet, indent=2, ensure_ascii=False) + "\n").encode(),
        )
        print(identifier, "primary annotation complete")
