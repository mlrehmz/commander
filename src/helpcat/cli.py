"""File-only command line interface."""

import argparse
import hashlib
from contextlib import nullcontext

from jsonschema import ValidationError
import json
import sys
from pathlib import Path

from . import parse_help, validate_catalog
from .engines import load_engine


def query(catalog, spelling):
    validate_catalog(catalog)
    records = [f for f in catalog["flags"] if spelling in [a["value"] for a in f["aliases"]]]
    return {
        "status": "not_found" if not records else "found" if len(records) == 1 else "ambiguous",
        "records": records,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(prog="helpcat")
    sub = parser.add_subparsers(dest="operation", required=True)
    parse = sub.add_parser("parse")
    parse.add_argument("input")
    parse.add_argument("--command", action="append", required=True)
    parse.add_argument("--engine", choices=["rules", "crf"], default="rules")
    parse.add_argument("--model")
    parse.add_argument("--policy")
    q = sub.add_parser("query")
    q.add_argument("catalog")
    q.add_argument("--flag", required=True)
    args = parser.parse_args(argv)
    try:
        if args.operation == "parse":
            with (
                Path(args.input).open("rb") if args.input != "-" else nullcontext(sys.stdin.buffer)
            ) as stream:
                digest = hashlib.sha256()
                raw = bytearray()
                for chunk in iter(lambda: stream.read(65536), b""):
                    digest.update(chunk)
                    raw.extend(chunk[: max(0, 1048577 - len(raw))])
                raw = bytes(raw)
            engine = load_engine(args.engine, model=args.model, policy=args.policy)
            try:
                text = raw.decode("utf-8")
            except UnicodeError:
                result = parse_help("", command_path=tuple(args.command), engine=engine)
                result["source"]["raw_sha256"] = hashlib.sha256(raw).hexdigest()
                result["diagnostics"] = ["invalid UTF-8 input"]
            else:
                result = parse_help(text, command_path=tuple(args.command), engine=engine)
            result["source"]["raw_sha256"] = digest.hexdigest()
            code = 1 if result["status"] == "failed" else 0
            for diagnostic in result["diagnostics"]:
                print(f"helpcat: {diagnostic}", file=sys.stderr)
        else:
            result = query(json.loads(Path(args.catalog).read_text(encoding="utf-8")), args.flag)
            code = 0
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    except (OSError, ValueError, ImportError) as exc:
        print(f"helpcat: {exc}", file=sys.stderr)
        return 2
    except ValidationError as exc:
        print(f"helpcat: invalid catalog: {exc.message}", file=sys.stderr)
        return 2
