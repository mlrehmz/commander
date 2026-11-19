"""Recheck source-survey claims against primary bytes, not agent summaries."""

import concurrent.futures
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen


def raw_url(url):
    parts = urlsplit(url)
    if parts.netloc == "github.com" and "/blob/" in parts.path:
        owner, repo, _, ref, *path = parts.path.strip("/").split("/")
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/" + ("/".join(path))
    return parts._replace(fragment="").geturl()


def main():
    requests = {}

    def add(url, digest, lines=(), local=None):
        url = raw_url(url)
        item = requests.setdefault(url, {"url": url, "sha256": digest, "lines": [], "local": []})
        if item["sha256"] != digest:
            raise ValueError("conflicting source hashes")
        item["lines"].extend(lines)
        if local:
            item["local"].append(local)

    cobra = json.loads(Path("collection/expansion/cobra-survey.json").read_text())
    for project in cobra["projects"]:
        evidence = json.loads(Path(project["family_evidence"]).read_text())
        for file in evidence["code_evidence"]:
            add(file["raw_url"], file["sha256"], [(e["line"], e["code"]) for e in file["excerpts"]])
        license = evidence["redistribution_evidence"]["license"]
        add(license["raw_url"], license["sha256"])
        for notice in evidence["redistribution_evidence"]["notice_files"]:
            add(notice["raw_url"], notice["sha256"])
    clap = json.loads(Path("collection/expansion/clap-survey.json").read_text())
    for project in clap["projects"]:
        for file in project["family_evidence"]:
            add(
                file["url"],
                file["upstream_file_sha256"],
                [(e["line"], e["text"]) for e in file["lines"]],
            )
        license = project["license_evidence"]
        file = license.get("manifest")
        if file:
            add(
                file["url"],
                file["upstream_file_sha256"],
                [(e["line"], e["text"]) for e in file["lines"]],
            )
        for notice in license["license_and_notice_files"]:
            add(notice["url"], notice["sha256"], local=notice["path"])

    def verify(item):
        try:
            raw = urlopen(item["url"], timeout=30).read()
            if hashlib.sha256(raw).hexdigest() != item["sha256"]:
                raise ValueError("upstream byte hash mismatch")
            lines = raw.decode("utf-8").splitlines()
            for number, text in item["lines"]:
                if lines[number - 1].strip() != text.strip():
                    raise ValueError("source excerpt mismatch")
            for path in item["local"]:
                if hashlib.sha256(Path(path).read_bytes()).hexdigest() != item["sha256"]:
                    raise ValueError("archived notice hash mismatch")
            return {
                "url": item["url"],
                "sha256": item["sha256"],
                "status": "verified",
                "excerpt_count": len(item["lines"]),
                "archived_notice_count": len(item["local"]),
            }
        except Exception as exc:
            return {"url": item["url"], "status": "failed", "diagnostic": str(exc)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(verify, requests.values()))
    result = {
        "version": 1,
        "scope": "Primary source bytes and cited excerpts only; no CLI help or binary execution.",
        "projects": len(cobra["projects"]) + len(clap["projects"]),
        "all_verified": all(r["status"] == "verified" for r in rows),
        "sources": rows,
    }
    Path("collection/expansion/source-verification.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "projects": result["projects"],
                "source_files": len(rows),
                "all_verified": result["all_verified"],
                "failures": [r for r in rows if r["status"] != "verified"],
            },
            indent=2,
        )
    )
    return 0 if result["all_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
