import json
import subprocess
import sys


def run(*args, text=""):
    return subprocess.run(
        [sys.executable, "-m", "helpcat", *args], input=text, text=True, capture_output=True
    )


def test_parse_query_and_errors(tmp_path):
    result = run("parse", "-", "--command", "demo", text="Options:\n  -v, --verbose  Details\n")
    assert result.returncode == 0, result.stderr
    cat = json.loads(result.stdout)
    path = tmp_path / "catalog.json"
    path.write_text(result.stdout)
    found = run("query", str(path), "--flag=-v")
    assert json.loads(found.stdout)["status"] == "found"
    assert json.loads(run("query", str(path), "--flag=-z").stdout)["status"] == "not_found"
    assert cat["flags"][0]["aliases"][0]["value"] == "-v"
    assert run("parse", "/no/such/file", "--command", "x").returncode == 2
    failed = run("parse", "-", "--command", "x", text="hello world")
    assert failed.returncode == 1
    assert json.loads(failed.stdout)["status"] == "failed"


def test_invalid_encoding_has_json_failure(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_bytes(b"\xff")
    result = run("parse", str(path), "--command", "demo")
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "failed"


def test_rules_engine_does_not_load_optional_ml_dependencies():
    code = (
        "from helpcat import ParserEngine, parse_help; import sys; "
        'parse_help("Options:\\n  -v  Details", command_path=("x",),engine=ParserEngine()); '
        'assert "torch" not in sys.modules; assert "pycrfsuite" not in sys.modules'
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
