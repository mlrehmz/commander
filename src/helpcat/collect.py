"""Offline, bounded container capture; never execute collected tools on the host."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import tempfile
import time
import uuid


def build_command(runtime, image, command, *, name=None):
    if not re.fullmatch(r"(?:sha256:|[^\s]+@sha256:)[a-f0-9]{64}", image):
        raise ValueError("collection image requires an immutable digest")
    if not command or any(not isinstance(arg, str) or "\0" in arg for arg in command):
        raise ValueError("invalid command vector")
    return [
        runtime,
        "run",
        "--rm",
        "--pull=never",
        "--name",
        name or "helpcat-" + uuid.uuid4().hex,
        "--read-only",
        "--network=none",
        "--memory=512m",
        "--memory-swap=512m",
        "--cpus=1",
        "--pids-limit=64",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--user=65534:65534",
        "--tmpfs=/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777",
        "--env=HOME=/tmp",
        "--env=LC_ALL=C.UTF-8",
        "--env=COLUMNS=80",
        "--env=TERM=dumb",
        "--env=NO_COLOR=1",
        "--workdir=/tmp",
        "--entrypoint=" + command[0],
        image,
        *command[1:],
    ]


def bounded_run(argv, *, timeout=20.0, max_bytes=1048576):
    if timeout <= 0 or max_bytes <= 0:
        raise ValueError("capture limits must be positive")
    started = time.monotonic()
    output = {"stdout": bytearray(), "stderr": bytearray()}
    status = "ok"
    with subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    ) as process:
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ, "stdout")
                selector.register(process.stderr, selectors.EVENT_READ, "stderr")
                while selector.get_map():
                    remaining = timeout - (time.monotonic() - started)
                    if remaining <= 0:
                        status = "timeout"
                        break
                    for key, _ in selector.select(min(0.1, remaining)):
                        chunk = os.read(key.fileobj.fileno(), 65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        if sum(map(len, output.values())) + len(chunk) > max_bytes:
                            status = "output_limit"
                            break
                        output[key.data].extend(chunk)
                    if status != "ok":
                        break
                if status == "ok":
                    try:
                        process.wait(timeout=max(0.001, timeout - (time.monotonic() - started)))
                    except subprocess.TimeoutExpired:
                        status = "timeout"
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        if process.returncode and status == "ok":
            status = "nonzero_exit"
        result = {key: bytes(value) for key, value in output.items()}
        return {
            **result,
            "status": status,
            "exit_code": process.returncode,
            "elapsed_seconds": time.monotonic() - started,
            "sha256": hashlib.sha256(result["stdout"]).hexdigest(),
        }


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f"refusing to replace different authoritative data: {path}")
        return
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        # Hard linking creates a new path and cannot replace an existing capture.
        os.link(temporary, path)
    finally:
        os.unlink(temporary)


def collect(plan, *, runtime="podman", output="corpus/intake"):
    from .core import canonicalize

    root = Path(output)
    results = []
    for item in plan["captures"]:
        identifier = item["id"]
        if not re.fullmatch("[a-z0-9][a-z0-9_-]*", identifier):
            raise ValueError("unsafe capture id")
        name = "helpcat-" + uuid.uuid4().hex
        command = build_command(runtime, plan["image"], item["invocation"], name=name)
        try:
            result = bounded_run(
                command,
                timeout=plan.get("timeout_seconds", 20),
                max_bytes=plan.get("output_limit_bytes", 1048576),
            )
        finally:
            # Remove a container even if its client exits before cleanup.
            subprocess.run(
                [runtime, "rm", "--force", name],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
            )
        if result["status"] == "ok":
            try:
                canonicalize(result["stdout"].decode("utf-8"))
            except (ValueError, UnicodeError) as exc:
                result["status"] = "invalid_text"
                result["diagnostic"] = str(exc)
        receipt = {
            **item,
            **{k: v for k, v in result.items() if k not in ("stdout", "stderr")},
            "image": plan["image"],
            "runtime_argv": command,
            "stderr": result["stderr"].decode("utf-8", errors="replace"),
            "locale": "C.UTF-8",
            "terminal_width": 80,
            "normalization_version": "1.0",
            "annotation_status": "pending",
            "split": None,
        }
        capture = root / (identifier + ".txt")
        if result["status"] == "ok":
            atomic_write(capture, result["stdout"])
        receipt_path = root / (identifier + ".receipt.json")
        if result["status"] != "ok":
            receipt_path = root / "failures" / (identifier + "-" + uuid.uuid4().hex + ".json")
        if receipt_path.exists():
            existing = json.loads(receipt_path.read_text())
            if existing["sha256"] != receipt["sha256"] or existing["image"] != receipt["image"]:
                raise ValueError("capture receipt conflict")
        else:
            atomic_write(receipt_path, (json.dumps(receipt, indent=2) + "\n").encode())
        results.append({"id": identifier, "status": result["status"], "sha256": result["sha256"]})
    return results


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--runtime", choices=["podman", "docker"], default="podman")
    parser.add_argument("--output", default="corpus/intake")
    args = parser.parse_args(argv)
    try:
        result = collect(
            json.loads(Path(args.plan).read_text()), runtime=args.runtime, output=args.output
        )
        print(json.dumps(result, indent=2))
        return 0 if all(r["status"] == "ok" for r in result) else 1
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"collection failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
