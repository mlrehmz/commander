"""Create provisional capture cohorts without opening any help contents."""

import json
from pathlib import Path

PY_TEST = {"coverage", "docutils", "pylint", "bandit", "httpx", "streamlink"}
PY_DEV = {"pytest", "ansible-core", "awscli", "poetry", "mypy", "isort", "llm"}
NATIVE_TEST = {"wget", "findutils", "gzip", "m4", "nano", "rsync"}
NATIVE_DEV = {"curl", "tar", "gawk", "less", "golang"}
COMMANDS = {
    "pytest": "pytest",
    "coverage": "coverage",
    "poetry": "poetry",
    "ansible-core": "ansible",
    "awscli": "aws",
    "pip": "pip",
    "pip-tools": "pip-compile",
    "pre-commit": "pre-commit",
    "cookiecutter": "cookiecutter",
    "mkdocs": "mkdocs",
    "sphinx": "sphinx-build",
    "docutils": "docutils",
    "mypy": "mypy",
    "pylint": "pylint",
    "isort": "isort",
    "autopep8": "autopep8",
    "flake8": "flake8",
    "bandit": "bandit",
    "yamllint": "yamllint",
    "codespell": "codespell",
    "twine": "twine",
    "build": "pyproject-build",
    "wheel": "wheel",
    "nox": "nox",
    "invoke": "invoke",
    "fabric": "fab",
    "streamlink": "streamlink",
    "httpx": "httpx",
    "llm": "llm",
    "yt-dlp": "yt-dlp",
}
IMAGE = "sha256:677773ee10313e9f3486b0eb729d13e27c2ca49f2b18ac6a72b7327867c2bbd3"


def main():
    root = Path("collection/expansion")
    python = json.loads((root / "python/environment-evidence.json").read_text())["projects"]
    native = json.loads((root / "native/environment-evidence.json").read_text())["projects"]
    native_source = {
        p["id"]: p for p in json.loads((root / "native-survey.json").read_text())["projects"]
    }
    cohorts = {split: [] for split in ("train", "dev", "familiar_test")}
    proposals = []
    for p in json.loads(Path("collection/survey.json").read_text())["projects"]:
        proposals.append(
            {"project": p["project"], "reserved_split": "train", "status": "audited_pilot"}
        )
    for p in python:
        name = p["package"]
        command = COMMANDS[name]
        if command not in p["bin_files"]:
            raise ValueError("unverified console script " + name)
        split = "familiar_test" if name in PY_TEST else "dev" if name in PY_DEV else "train"
        invocation = [p["prefix"] + "/bin/" + command, "--help"]
        if name == "awscli":
            invocation = ["env", "PAGER=cat", "AWS_PAGER=", p["prefix"] + "/bin/aws", "help"]
        if name == "pytest":
            invocation = ["env", "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1", *invocation]
        item = {
            "id": name + "-root",
            "project": name,
            "package": name,
            "tool_version": p["version"],
            "invocation": invocation,
            "command_path": [command],
            "family": "unknown",
            "leakage_group": "invoke-fabric"
            if name in ("invoke", "fabric")
            else "pip-tooling"
            if name in ("pip", "pip-tools")
            else name,
            "source_url": f"https://pypi.org/project/{name}/{p['version']}/",
            "license_evidence": "collection/expansion/python/environment-evidence.json",
            "reserved_split": split,
            "split_status": "provisional_pending_grouping",
            "synthetic": False,
        }
        cohorts[split].append(item)
        proposals.append({"project": name, "reserved_split": split, "status": "capture_planned"})
    for p in native:
        name = p["id"]
        command = Path(p["binary_path"]).name
        split = "familiar_test" if name in NATIVE_TEST else "dev" if name in NATIVE_DEV else "train"
        invocation = [p["binary_path"], "--help"]
        stream = "stdout"
        codes = [0]
        if name == "curl":
            invocation.append("all")
        if name == "golang":
            invocation = [p["binary_path"], "-h"]
            stream = "stderr"
            codes = [0, 2]
        if name == "tmux":
            invocation = [p["binary_path"], "-h"]
            stream = "stderr"
            codes = [1]
        source = native_source[name]
        item = {
            "id": name + "-root",
            "project": name,
            "tool_version": p["package"]["version"],
            "version_source": "debian_package",
            "invocation": invocation,
            "command_path": [command],
            "family": source["family"],
            "leakage_group": name,
            "source_url": source["source_url"],
            "license_evidence": "collection/expansion/native/environment-evidence.json",
            "capture_stream": stream,
            "accepted_exit_codes": codes,
            "reserved_split": split,
            "split_status": "provisional_pending_grouping",
            "synthetic": False,
            "binary_sha256": p["binary_sha256"],
        }
        if name == "tmux":
            item["capture_kind"] = "explicit_diagnostic_usage_on_invalid_help_option"
        cohorts[split].append(item)
        proposals.append({"project": name, "reserved_split": split, "status": "capture_planned"})
    for family in ("cobra", "clap"):
        data = json.loads((root / (family + "-survey.json")).read_text())
        for p in data["projects"]:
            proposals.append(
                {
                    "project": p["project"],
                    "reserved_split": family + "_test",
                    "status": "asset_verified_help_unopened",
                }
            )
    counts = {
        split: sum(p["reserved_split"] == split for p in proposals)
        for split in ("train", "dev", "familiar_test", "cobra_test", "clap_test")
    }
    if counts != {"train": 36, "dev": 12, "familiar_test": 12, "cobra_test": 20, "clap_test": 20}:
        raise ValueError("proposal counts mismatch")
    (root / "split-proposal.json").write_text(
        json.dumps(
            {
                "version": 1,
                "frozen": False,
                "status": "PROVISIONAL: no evaluation admission",
                "why": "Reserve familiar test projects before capture so development need not open their help.",
                "counts": counts,
                "grouping_review_complete": False,
                "projects": proposals,
            },
            indent=2,
        )
        + "\n"
    )
    for split, items in cohorts.items():
        (root / (split + "-plan.json")).write_text(
            json.dumps(
                {
                    "version": 1,
                    "image": IMAGE,
                    "timeout_seconds": 20,
                    "output_limit_bytes": 1048576,
                    "captures": items,
                },
                indent=2,
            )
            + "\n"
        )
    print(
        "Prepared 50 capture requests and a provisional 100-project reservation; no help text read."
    )


if __name__ == "__main__":
    main()
