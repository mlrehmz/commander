"""Run inside the image: read package metadata/source, never import collected apps."""

import ast
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import re
import sys

requests = json.loads(sys.argv[1])
isolated = sys.argv[2] == "isolated"
rows = []
for item in requests:
    name = item["package"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        raise ValueError("invalid package name")
    prefix = Path("/opt/tools") / name if isolated else Path("/usr/local")
    site = prefix / "lib/python3.12/site-packages"

    def normalize(value):
        return re.sub("[-_.]+", "-", value).lower()

    dist = next(
        d
        for d in metadata.distributions(path=[str(site)])
        if normalize(d.metadata["Name"]) == normalize(name)
    )
    if dist.version != item["version"]:
        raise ValueError("installed package version mismatch")
    entrypoints = [
        {"name": e.name, "value": e.value}
        for e in dist.entry_points
        if e.group == "console_scripts"
    ]
    namespaces = {e["value"].split(":")[0].split(".")[0] for e in entrypoints}
    namespaces.add(name.replace("-", "_"))
    notices = []
    evidence = []
    man = []
    completion = []
    for path in dist.files or []:
        label = str(path)
        if ".dist-info/" in label and any(
            w in label.lower() for w in ("license", "copying", "notice")
        ):
            raw = dist.locate_file(path).read_bytes()
            notices.append(
                {
                    "path": label,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "text": raw.decode("utf-8"),
                }
            )
        if "/man/" in label:
            man.append(label)
        if "completion" in label.lower():
            completion.append(label)
        if not label.endswith(".py") or label.split("/")[0] not in namespaces:
            continue
        raw = dist.locate_file(path).read_bytes()
        if len(raw) > 1048576 or not any(
            word in raw
            for word in (b"argparse", b"click", b"optparse", b"typer", b"cleo", b"cliff", b"docopt")
        ):
            continue
        try:
            tree = ast.parse(raw.decode("utf-8"))
        except (SyntaxError, UnicodeError):
            continue
        aliases = {}
        imports = []
        calls = []
        lines = raw.decode("utf-8").splitlines()
        families = (
            "argparse",
            "click",
            "optparse",
            "rich_click",
            "typer",
            "cleo",
            "cliff",
            "docopt",
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in families:
                        aliases[alias.asname or root] = root
                        imports.append(node.lineno)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for family in families:
                    if family in module.split("."):
                        for alias in node.names:
                            aliases[alias.asname or alias.name] = family
                        imports.append(node.lineno)
                    elif any(alias.name == family for alias in node.names):
                        for alias in node.names:
                            if alias.name == family:
                                aliases[alias.asname or alias.name] = family
                        imports.append(node.lineno)
        for node in ast.walk(tree):
            targets = (
                [node.func]
                if isinstance(node, ast.Call)
                else node.bases
                if isinstance(node, ast.ClassDef)
                else []
            )
            for target in targets:
                root = target
                while isinstance(root, ast.Attribute):
                    root = root.value
                if isinstance(root, ast.Name) and root.id in aliases:
                    calls.append(
                        {
                            "line": node.lineno,
                            "family": aliases[root.id],
                            "text": lines[node.lineno - 1].strip(),
                        }
                    )
        if imports and calls:
            evidence.append(
                {
                    "path": label,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "imports": [
                        {"line": n, "text": lines[n - 1].strip()} for n in sorted(set(imports))
                    ],
                    "calls": calls[:12],
                }
            )
    rows.append(
        {
            "package": name,
            "version": dist.version,
            "prefix": str(prefix),
            "entrypoints": entrypoints,
            "bin_files": sorted(p.name for p in (prefix / "bin").iterdir()),
            "notices": notices,
            "family_source_candidates": evidence,
            "wheel_man_files": man,
            "wheel_completion_files": completion,
            "machine_readable_spec_surface": None,
        }
    )
print(json.dumps(rows))
