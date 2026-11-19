import hashlib
import sys

import pytest

from helpcat.collect import build_command, bounded_run


def test_container_contract_and_digest():
    args = build_command("podman", "sha256:" + "a" * 64, ["black", "--help"])
    for value in (
        "--read-only",
        "--network=none",
        "--memory=512m",
        "--cpus=1",
        "--pids-limit=64",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
    ):
        assert value in args
    assert "--entrypoint=black" in args
    assert args[-1] == "--help"
    with pytest.raises(ValueError, match="digest"):
        build_command("podman", "python:latest", ["black", "--help"])


def test_bounded_process_success_and_failures():
    result = bounded_run([sys.executable, "-c", 'print("hello")'], timeout=5, max_bytes=100)
    assert result["stdout"] == b"hello\n"
    assert result["status"] == "ok"
    assert result["sha256"] == hashlib.sha256(b"hello\n").hexdigest()
    result = bounded_run([sys.executable, "-c", 'print("x"*10000)'], timeout=5, max_bytes=100)
    assert result["status"] == "output_limit"
    result = bounded_run(
        [sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.1, max_bytes=100
    )
    assert result["status"] == "timeout"


def test_capture_receipt_and_retry(tmp_path):
    import json
    from helpcat.collect import collect

    runtime = tmp_path / "runtime"
    runtime.write_text(
        "#!"
        + sys.executable
        + '\nimport sys\nif sys.argv[1] == "run": print("Options:\\n  -v  Details")\n'
    )
    runtime.chmod(0o755)
    plan = {
        "image": "sha256:" + "a" * 64,
        "captures": [{"id": "demo", "invocation": ["demo", "--help"], "project": "demo"}],
    }
    output = tmp_path / "intake"
    assert collect(plan, runtime=str(runtime), output=output)[0]["status"] == "ok"
    receipt = json.loads((output / "demo.receipt.json").read_text())
    raw = (output / "demo.txt").read_bytes()
    assert receipt["sha256"] == hashlib.sha256(raw).hexdigest()
    assert receipt["annotation_status"] == "pending"
    assert receipt["split"] is None
    assert collect(plan, runtime=str(runtime), output=output)[0]["status"] == "ok"
    (output / "demo.txt").write_text("other")
    with pytest.raises(ValueError, match="refusing"):
        collect(plan, runtime=str(runtime), output=output)


def test_failed_attempt_does_not_block_successful_retry(tmp_path):
    from helpcat.collect import collect

    runtime = tmp_path / "runtime"

    def write(code):
        runtime.write_text(
            "#!" + sys.executable + '\nimport sys\nif sys.argv[1] == "run":\n ' + code + "\n"
        )
        runtime.chmod(0o755)

    plan = {
        "image": "sha256:" + "a" * 64,
        "captures": [{"id": "demo", "invocation": ["demo", "--help"]}],
    }
    output = tmp_path / "intake"
    write("sys.exit(1)")
    assert collect(plan, runtime=str(runtime), output=output)[0]["status"] == "nonzero_exit"
    assert not (output / "demo.receipt.json").exists()
    write('print("Options:\\n  -v  Details")')
    assert collect(plan, runtime=str(runtime), output=output)[0]["status"] == "ok"
    assert (output / "demo.receipt.json").exists()


def test_explicit_stderr_help_and_exit_policy(tmp_path):
    import json
    from helpcat.collect import collect

    runtime = tmp_path / "runtime"
    runtime.write_text(
        "#!"
        + sys.executable
        + '\nimport sys\nif sys.argv[1]=="run":\n print("Usage: demo\\n  -h  Help",file=sys.stderr)\n sys.exit(2)\n'
    )
    runtime.chmod(0o755)
    item = {
        "id": "demo",
        "invocation": ["demo", "-h"],
        "capture_stream": "stderr",
        "accepted_exit_codes": [0, 2],
    }
    plan = {"image": "sha256:" + "a" * 64, "captures": [item]}
    output = tmp_path / "intake"
    assert collect(plan, runtime=str(runtime), output=output)[0]["status"] == "ok"
    raw = (output / "demo.txt").read_bytes()
    assert raw.startswith(b"Usage: demo")
    receipt = json.loads((output / "demo.receipt.json").read_text())
    assert receipt["exit_code"] == 2
    assert receipt["sha256"] == hashlib.sha256(raw).hexdigest()
    assert receipt["stdout_sha256"] == hashlib.sha256(b"").hexdigest()
    assert receipt["stderr_sha256"] == receipt["sha256"]
    item["id"] = "unaccepted"
    item["accepted_exit_codes"] = [0]
    assert collect(plan, runtime=str(runtime), output=output)[0]["status"] == "nonzero_exit"


def test_empty_capture_is_not_a_success(tmp_path):
    from helpcat.collect import collect

    runtime = tmp_path / "runtime"
    runtime.write_text("#!" + sys.executable + "\n")
    runtime.chmod(0o755)
    plan = {
        "image": "sha256:" + "a" * 64,
        "captures": [{"id": "empty", "invocation": ["demo", "--help"]}],
    }
    output = tmp_path / "intake"
    assert collect(plan, runtime=str(runtime), output=output)[0]["status"] == "empty_output"
    assert not (output / "empty.txt").exists()
