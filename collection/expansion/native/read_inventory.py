"""Inspect prepared native artifacts and notices without running collected tools."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys

requests = json.loads(sys.argv[1])
lock = json.loads(Path("/opt/helpcat/native-lock.json").read_text())
prepared = {row["package"]: row for row in lock["packages"]}
base = {}
query = subprocess.check_output(
    ["dpkg-query", "-W", "-f=${Package}\t${Version}\t${Architecture}\t${source:Package}\n"],
    text=True,
)
for line in query.splitlines():
    name, version, arch, source = line.split("\t")
    base[name] = {
        "package": name,
        "version": version,
        "architecture": arch,
        "source": source,
        "artifact_origin": "digest-pinned-base-image",
        "download_url": None,
        "sha256": None,
    }
paths = {
    "curl": "/usr/bin/curl",
    "wget": "/usr/bin/wget",
    "tar": "/usr/bin/tar",
    "grep": "/usr/bin/grep",
    "sed": "/usr/bin/sed",
    "gawk": "/usr/bin/gawk",
    "diffutils": "/usr/bin/diff",
    "findutils": "/usr/bin/find",
    "gzip": "/usr/bin/gzip",
    "xz": "/usr/bin/xz",
    "make": "/usr/bin/make",
    "patch": "/usr/bin/patch",
    "m4": "/usr/bin/m4",
    "less": "/usr/bin/less",
    "nano": "/usr/bin/nano",
    "tmux": "/usr/bin/tmux",
    "htop": "/usr/bin/htop",
    "rsync": "/usr/bin/rsync",
    "file": "/usr/bin/file",
}
rows = []
for item in requests:
    name = item["id"]
    provider = item["debian_binary_package"]
    if name == "golang":
        candidates = list(Path("/usr/lib").glob("go-*/bin/gofmt"))
        if len(candidates) != 1:
            raise ValueError("ambiguous Go toolchain")
        path = candidates[0]
    else:
        path = Path(paths[name])
    if not path.is_file():
        raise ValueError("missing binary " + str(path))
    package = prepared.get(provider) or base.get(provider)
    if not package:
        raise ValueError("missing provider version")
    notice = Path("/usr/share/doc") / provider / "copyright"
    if not notice.is_file():
        raise ValueError("missing package copyright")
    raw = notice.read_bytes()
    rows.append(
        {
            "id": name,
            "project": item["project"],
            "binary_path": str(path),
            "binary_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "package": package,
            "copyright_path": str(notice),
            "copyright_sha256": hashlib.sha256(raw).hexdigest(),
            "copyright_text": raw.decode("utf-8"),
            "man_page_in_image": any(Path("/usr/share/man").glob("man*/" + path.name + ".*")),
        }
    )
licenses = []
for path in sorted(Path("/usr/share/common-licenses").iterdir()):
    if path.is_file() and not path.is_symlink():
        raw = path.read_bytes()
        licenses.append(
            {
                "name": path.name,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "text": raw.decode("utf-8"),
            }
        )
print(json.dumps({"downloaded_artifact_lock": lock, "projects": rows, "common_licenses": licenses}))
