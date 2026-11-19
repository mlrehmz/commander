"""Resolve each captured project separately to avoid dependency interference."""

import concurrent.futures
import json
import os
from pathlib import Path
import subprocess


def main():
    root = Path(__file__).parent
    rows = json.loads((root / "package-metadata.json").read_text())
    folder = root / "locks"
    folder.mkdir(exist_ok=True)

    def resolve(row):
        name = row["package"]
        requirement = folder / (name + ".in")
        requirement.write_text(f"{name}=={row['version']}\n")
        result = subprocess.run(
            [
                "uv",
                "pip",
                "compile",
                str(requirement),
                "--python-version",
                "3.12",
                "--generate-hashes",
                "--only-binary",
                ":all:",
                "--quiet",
                "-o",
                str(folder / (name + ".lock")),
            ],
            capture_output=True,
            text=True,
            env=dict(os.environ),
        )
        (folder / (name + ".resolution.log")).write_text(result.stderr)
        return {"package": name, "version": row["version"], "locked": result.returncode == 0}

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(resolve, rows))
    (root / "resolution-results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))
    return 0 if all(row["locked"] for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
