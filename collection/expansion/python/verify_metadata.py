import concurrent.futures
import json
import urllib.request
import hashlib
from pathlib import Path
from packaging.specifiers import SpecifierSet, InvalidSpecifier
from packaging.version import Version, InvalidVersion

packages = [
    "pytest",
    "coverage",
    "poetry",
    "ansible-core",
    "awscli",
    "pip",
    "pip-tools",
    "pre-commit",
    "cookiecutter",
    "mkdocs",
    "sphinx",
    "docutils",
    "mypy",
    "pylint",
    "isort",
    "autopep8",
    "flake8",
    "bandit",
    "yamllint",
    "codespell",
    "twine",
    "build",
    "wheel",
    "nox",
    "invoke",
    "fabric",
    "streamlink",
    "httpx",
    "llm",
    "yt-dlp",
]
root = Path(__file__).parent


def fetch(name):
    url = f"https://pypi.org/pypi/{name}/json"
    raw = urllib.request.urlopen(url, timeout=30).read()
    data = json.loads(raw)
    versions = []
    for value, files in data["releases"].items():
        try:
            v = Version(value)
        except InvalidVersion:
            continue
        if v.is_prerelease or v.is_devrelease:
            continue
        supported = False
        for f in files:
            try:
                if (
                    f["packagetype"] == "bdist_wheel"
                    and not f.get("yanked")
                    and Version("3.12.15") in SpecifierSet(f.get("requires_python") or "")
                ):
                    supported = True
            except InvalidSpecifier:
                continue
        if supported:
            versions.append(v)
    version = str(max(versions))
    fixed_url = f"https://pypi.org/pypi/{name}/{version}/json"
    fixed = urllib.request.urlopen(fixed_url, timeout=30).read()
    metadata = json.loads(fixed)
    info = metadata["info"]
    (root / (name + ".pypi.json")).write_bytes(fixed)
    license = (
        info.get("license_expression")
        or info.get("license")
        or [c for c in info["classifiers"] if c.startswith("License ::")]
    )
    return {
        "package": name,
        "version": version,
        "source_url": fixed_url,
        "metadata_sha256": hashlib.sha256(fixed).hexdigest(),
        "requires_python": info.get("requires_python"),
        "license_metadata": license,
        "project_urls": info.get("project_urls"),
        "status": "metadata_verified",
    }


with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    rows = list(pool.map(fetch, packages))
(root / "package-metadata.json").write_text(json.dumps(rows, indent=2) + "\n")
(root / "requirements.in").write_text(
    "".join(r["package"] + "==" + r["version"] + "\n" for r in rows)
)
for row in rows:
    print(row["package"], row["version"], str(row["license_metadata"])[:70])
