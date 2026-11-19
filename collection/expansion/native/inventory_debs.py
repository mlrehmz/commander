"""Record fetched Debian artifact identities without running their programs."""

import hashlib
import json
from pathlib import Path
import shlex
import subprocess

rows = []
for path in sorted(Path("/var/cache/apt/archives").glob("*.deb")):
    fields = {}
    result = subprocess.check_output(["dpkg-deb", "--field", str(path)], text=True)
    for line in result.splitlines():
        if line and not line.startswith(" ") and ": " in line:
            key, value = line.split(": ", 1)
            fields[key] = value
    package, version = fields["Package"], fields["Version"]
    uri_output = subprocess.check_output(
        ["apt-get", "--print-uris", "download", package + "=" + version], text=True
    )
    uri_lines = [line for line in uri_output.splitlines() if line.startswith("'")]
    if len(uri_lines) != 1:
        raise ValueError("ambiguous package URI")
    uri = shlex.split(uri_lines[0])[0]
    rows.append(
        {
            "package": package,
            "version": version,
            "architecture": fields["Architecture"],
            "source": fields.get("Source", package),
            "filename": path.name,
            "download_url": uri,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    )
Path("/opt/helpcat/native-lock.json").write_text(
    json.dumps({"version": 1, "packages": rows}, indent=2) + "\n"
)
