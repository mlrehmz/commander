"""One assembly path shared by all line taggers."""

from dataclasses import dataclass, field as dc_field
import re

from .core import LABELS, canonicalize, field, validate_catalog

TOKEN = re.compile(r"--(?:\[no-\])?[A-Za-z0-9][\w-]*|-[A-Za-z0-9?]")
META_ATOM = r"[A-Za-z_][A-Za-z0-9_:.-]*(?:,[A-Za-z0-9_:.-]+)*(?:\[[^\[\]]+\])?"
META = re.compile(
    r"<[^<>\s]+>|\{[^{}]+\}|\[[^\[\]]+\]|"
    + META_ATOM
    + r"(?: +RANGE| +\[[^\]]+\]| +\| +"
    + META_ATOM
    + r")?"
    + r"(?=$| {2,}|\t|\s*[,|/]\s*-)"
)
HEADING = re.compile(r"^\s*([A-Za-z][\w /-]*):\s*$")

ENTRY = re.compile(r"^\s*([A-Za-z0-9_][\w.*-]*)(?: +\(([\w,-]+)\))?(?:(?: {2,}|\t+)(\S.*))?\s*$")
BOX_HEADING = re.compile(r"^\s*[╭┌┏][─━ -]*([A-Za-z][A-Za-z ]*?)[─━ -]*[╮┐┓]\s*$")


def content_bounds(line):
    start = len(line) - len(line.lstrip())
    end = len(line.rstrip())
    boxed = (
        start < end and line[start] in "│┃|" and line[end - 1] == line[start] and end - start > 1
    )
    if boxed:
        start += 1
        end -= 1
        start += len(line[start:end]) - len(line[start:end].lstrip())
        end = len(line[:end].rstrip())
    return start, end, boxed


def tokenize(line):
    """Read a declaration prefix; leave prose to the assembler."""
    pos, content_end, boxed = content_bounds(line)
    line = line[:content_end]
    tokens, meta, arity = [], None, "unknown"
    end = pos
    while True:
        match = TOKEN.match(line, pos)
        if not match:
            break
        tokens.append((match.group(), match.start(), match.end()))
        pos = end = match.end()
        value = None
        if line[pos : pos + 2] == "[=":
            close = line.find("]", pos + 2)
            if close < 0:
                return None
            value = (pos + 2, close)
            end = pos = close + 1
            arity = "optional"
        else:
            value_pos = pos
            if line[pos : pos + 1] == "=":
                value_pos += 1
            elif line[pos : pos + 1] == " " and line[pos : pos + 2] != "  ":
                value_pos += 1
            m = (
                META.match(line, value_pos)
                if value_pos > pos or line[pos : pos + 1] in "<[{"
                else None
            )
            if m:
                value = (m.start(), m.end())
                end = pos = m.end()
                arity = "required"
                if m.group().startswith("["):
                    arity = (
                        "optional" if re.fullmatch(r"\[[A-Z][A-Z0-9_]*\]", m.group()) else "unknown"
                    )
        if value:
            meta = value
        separator = (
            re.match(r"(?:\s*[,|/]\s*| +)(?=-)", line[pos:])
            if boxed
            else re.match(r"(?:\s*[,|/]\s*| )(?=-)", line[pos:])
        )
        if separator:
            pos += separator.end()
            continue
        break
    if not tokens:
        return None
    rest = line[end:]
    if rest.strip() and not re.match(r"(?: {2,}|\t+)", rest):
        return None
    desc = end + len(rest) - len(rest.lstrip())
    return tokens, meta, arity, desc


class RulesTagger:
    name = "rules"

    def predict(self, lines):
        output, section, active = [], "", False
        declaration_indent = 0
        usage_active = False
        for line in lines:
            start, end, boxed = content_bounds(line)
            stripped = line[start:end]
            indent = len(line[:start].expandtabs())
            heading = HEADING.match(line) or BOX_HEADING.match(line)
            entry = ENTRY.fullmatch(line.rstrip())
            if not stripped:
                label = "blank"
                usage_active = False
            elif stripped.lower().startswith("usage:") or (usage_active and line[:1].isspace()):
                label, active, usage_active = "usage", False, True
            elif heading and (
                not active or indent <= declaration_indent or BOX_HEADING.match(line)
            ):
                section = heading[1].strip().lower()
                label, active, usage_active = "section_heading", False, False
            elif active and indent > declaration_indent and not boxed:
                label = "description_continuation"
            elif (
                (line[:1].isspace() or boxed)
                and tokenize(line.rstrip().removesuffix(","))
                and section not in ("examples", "example", "usage examples")
            ):
                label, active = "option_declaration", True
                declaration_indent = indent
            elif (
                entry
                and line[:1].isspace()
                and section in ("commands", "subcommands", "available commands")
            ):
                label, active = "subcommand_declaration", True
                declaration_indent = indent
            elif (
                entry
                and line[:1].isspace()
                and section in ("arguments", "positionals", "positional arguments")
            ):
                label, active = "positional_declaration", True
                declaration_indent = indent
            elif active and (line[:1].isspace() or boxed):
                label = "description_continuation"
            else:
                label, active, usage_active = "prose", False, False
            output.append((label, 1.0))
        return output


@dataclass
class ParserEngine:
    tagger: object = dc_field(default_factory=RulesTagger)
    threshold: float = 0.0
    version: str = "rules-2"
    calibrated: bool = False

    def __post_init__(self):
        if not 0 <= self.threshold <= 1:
            raise ValueError("threshold must be in [0,1]")


def literal_semantics(lines, record):
    meta = record["metavar"]
    if meta and len(meta["evidence"]) == 1:
        literal = meta["literal"]
        delimiters = literal[:1], literal[-1:]
        inner = literal[1:-1]
        comma = delimiters == ("{", "}") and re.fullmatch(r"[\w.+-]+(?:,[\w.+-]+)+", inner)
        pipe = delimiters == ("[", "]") and re.fullmatch(r"[\w.+-]+(?:\|[\w.+-]+)+", inner)
        if comma or pipe:
            span = meta["evidence"][0]
            record["choices"] = field(lines, [(span["line"], span["start"] + 1, span["end"] - 1)])
    description = record["description"]
    if not description:
        return
    defaults = []
    for span in description["evidence"]:
        text = lines[span["line"] - 1][span["start"] : span["end"]]
        for pattern in (r"\(default: *([^()\n]+)\)", r"\[default: *([^\[\]\n]+)\]"):
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                literal = match[1]
                start = span["start"] + match.start(1) + len(literal) - len(literal.lstrip())
                end = span["start"] + match.start(1) + len(literal.rstrip())
                if start < end:
                    defaults.append(field(lines, [(span["line"], start, end)]))
    if len(defaults) == 1:
        record["default"] = defaults[0]


def assemble(source, command_path, predictions, engine):
    lines = source["canonical_text"].split("\n")
    if len(predictions) != len(lines) or any(
        label not in LABELS or not 0 <= score <= 1 for label, score in predictions
    ):
        raise ValueError("invalid tagger output")
    cat = {
        "schema_version": "1.0",
        "command_path": list(command_path),
        "source": source,
        "flags": [],
        "subcommands": [],
        "positionals": [],
        "status": "failed",
        "diagnostics": [],
        "engine": {
            "name": engine.tagger.name,
            "version": engine.version,
            "threshold": engine.threshold,
            "calibrated": engine.calibrated,
        },
    }
    active = None
    active_records = []
    declaration_indent = 0
    seen = {}
    pending = []
    recognized = False
    for idx, (line, (label, score)) in enumerate(zip(lines, predictions), 1):
        if label in ("usage", "section_heading"):
            recognized = True
        if label in ("option_declaration", "option_continuation"):
            if line.rstrip().endswith(","):
                prefix = tokenize(line.rstrip()[:-1])
                if prefix and score >= engine.threshold:
                    pending.extend(field(lines, [(idx, a, b)]) for _, a, b in prefix[0])
                    active = None
                    continue
            parsed = tokenize(line)
            if not parsed or score < engine.threshold:
                cat["diagnostics"].append(f"line {idx}: ambiguous or rejected declaration")
                active = None
                continue
            tokens, meta, arity, desc = parsed
            _, content_end, _ = content_bounds(line)
            aliases, pending = pending, []
            for value, start, end in tokens:
                if "[no-]" in value:
                    for expanded in (value.replace("[no-]", ""), value.replace("[no-]", "no-")):
                        aliases.append(
                            field(
                                lines, [(idx, start, end)], value=expanded, rule="expand-negatable"
                            )
                        )
                else:
                    aliases.append(field(lines, [(idx, start, end)]))
            record = {
                "aliases": aliases,
                "metavar": field(lines, [(idx, *meta)]) if meta else None,
                "arity": field(
                    lines,
                    [(idx, tokens[0][1], desc if desc > tokens[0][1] else tokens[-1][2])],
                    value=arity,
                    rule="declaration-value-notation",
                )
                if arity != "unknown"
                else None,
                "takes_value": True if arity in ("required", "optional") else None,
                "required_presence": None,
                "type": None,
                "default": None,
                "choices": None,
                "description": field(lines, [(idx, desc, content_end)])
                if desc < content_end
                else None,
                "selection_score": score,
            }
            names = tuple(a["value"] for a in aliases)
            if len(names) != len(set(names)):
                cat["diagnostics"].append(f"line {idx}: duplicate alias in declaration omitted")
                active = None
                continue
            overlaps = [seen[n] for n in names if n in seen]
            if overlaps:
                old = overlaps[0]
                if (
                    len(overlaps) != len(names)
                    or {a["value"] for a in old["aliases"]} != set(names)
                    or any(
                        old[k] and record[k] and old[k]["value"] != record[k]["value"]
                        for k in ("metavar", "arity", "description")
                    )
                ):
                    cat["diagnostics"].append(f"line {idx}: conflicting repeated option omitted")
                active = None
                continue
            cat["flags"].append(record)
            for name in names:
                seen[name] = record
            active = record
            active_records = [record]
            declaration_indent = len(line[: content_bounds(line)[0]].expandtabs())
            recognized = True
        elif label in ("subcommand_declaration", "positional_declaration"):
            m = ENTRY.fullmatch(line.rstrip())
            if not m or score < engine.threshold:
                cat["diagnostics"].append(f"line {idx}: rejected advertised entry")
                active = None
                continue
            spans = [(m.start(1), m.end(1))]
            if m.group(2) and label == "subcommand_declaration":
                spans.extend(
                    (m.start(2) + part.start(), m.start(2) + part.end())
                    for part in re.finditer(r"[\w-]+", m.group(2))
                )
            active_records = []
            for start, end in spans:
                record = {
                    "name": field(lines, [(idx, start, end)]),
                    "description": field(lines, [(idx, m.start(3), m.end(3))])
                    if m.group(3)
                    else None,
                    "selection_score": score,
                }
                cat["subcommands" if label == "subcommand_declaration" else "positionals"].append(
                    record
                )
                active_records.append(record)
            active = active_records[0]
            declaration_indent = len(line[: content_bounds(line)[0]].expandtabs())
            recognized = True
        elif label == "description_continuation" and active:
            start, end, _ = content_bounds(line)
            indent = len(line[:start].expandtabs())
            if indent <= declaration_indent:
                cat["diagnostics"].append(f"line {idx}: uncertain continuation omitted")
                active = None
                continue
            if start < end:
                spans = (
                    []
                    if active["description"] is None
                    else [
                        (s["line"], s["start"], s["end"]) for s in active["description"]["evidence"]
                    ]
                )
                spans.append((idx, start, end))
                literal = "\n".join(lines[n - 1][a:b] for n, a, b in spans)
                description = field(
                    lines,
                    spans,
                    value=" ".join(literal.split()),
                    rule="join-description-whitespace",
                )
                for record in active_records:
                    record["description"] = description
        elif label == "blank":
            if pending:
                cat["diagnostics"].append(f"line {idx}: incomplete wrapped declaration")
                pending = []
        else:
            if pending:
                cat["diagnostics"].append(f"line {idx}: incomplete wrapped declaration")
                pending = []
            active = None
            if re.match(r"^\s*(?:[│┃|]\s*)?-", line) and label not in ("blank", "usage"):
                cat["diagnostics"].append(f"line {idx}: unsupported flag-like candidate")
    if pending:
        cat["diagnostics"].append("incomplete wrapped declaration")
    cat["status"] = ("partial" if cat["diagnostics"] else "ok") if recognized else "failed"
    if not recognized:
        cat["diagnostics"].append("no recognizable help structure")
    for record in cat["flags"]:
        literal_semantics(lines, record)
    return validate_catalog(cat)


def parse_help(text: str, *, command_path: tuple[str, ...], engine: ParserEngine) -> dict:
    if not command_path or any(not isinstance(p, str) or not p.strip() for p in command_path):
        raise ValueError("command_path must contain nonempty strings")
    try:
        source = canonicalize(text)
    except ValueError as exc:
        import hashlib

        raw = text.encode("utf-8", errors="surrogatepass") if isinstance(text, str) else b""
        source = {
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "canonical_sha256": hashlib.sha256(b"").hexdigest(),
            "canonical_text": "",
            "normalization_version": "1.0",
            "capture_metadata": {},
        }
        cat = assemble(source, command_path, [("blank", 1.0)], engine)
        cat["diagnostics"] = [str(exc)]
        return cat
    return assemble(
        source, command_path, engine.tagger.predict(source["canonical_text"].split("\n")), engine
    )
