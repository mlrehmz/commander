"""Verify capture bytes and prepare a source-only annotation inventory."""
import hashlib
import json
import re
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPANSION = ROOT / "collection/expansion"
GROUPS = (
    {"pip", "pip-tools", "pipenv"},
    {"invoke", "fabric"},
    {"containers/podman", "containers/buildah", "containers/skopeo", "docker/cli", "containerd/nerdctl"},
    {"anchore/syft", "anchore/grype"},
    {"sigstore/cosign", "sigstore/rekor"},
)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    pilot = load(ROOT / "corpus/manifests/pilot.json")["entries"]
    proposal = load(EXPANSION / "split-proposal.json")
    assignments = {row["project"]: row["reserved_split"] for row in proposal["projects"]}
    python = {
        row["project"]: row for row in load(EXPANSION / "python-family-survey.json")["projects"]
    }
    native = {
        row["project"]: row for row in load(EXPANSION / "native-survey.json")["projects"]
    }
    audited = {row["id"]: row for row in pilot}
    rows = []
    shingles = {}
    captures = []
    for plan in sorted(EXPANSION.glob("*-plan.json")):
        for item in load(plan)["captures"]:
            captures.append(item)
    planned = {item["id"]: item for item in captures}
    receipts = sorted((ROOT / "corpus/intake").glob("*.receipt.json"))
    receipts += sorted((ROOT / "corpus/intake/expansion").glob("*/*.receipt.json"))
    for family in ("cobra", "clap"):
        receipts += sorted((ROOT / ".helpcat-heldout" / family).glob("*.receipt.json"))
    for path in receipts:
        stored = load(path)
        item = {**planned.get(stored["id"], {}), **stored}
        capture = path.with_name(path.name.removesuffix(".receipt.json") + ".txt")
        if digest(capture) != item["sha256"]:
            raise ValueError(f"Capture differs from its receipt: {capture.name}")
        project = item["project"]
        tokens = re.findall(r"[\w-]+", capture.read_text(encoding="utf-8").casefold())
        shingles[project] = set(zip(tokens, tokens[1:], tokens[2:], tokens[3:], tokens[4:]))
        family = item.get("family", "unknown")
        source = python.get(project) or native.get(project)
        if source:
            family = source.get("formatter_family") or source.get("family") or "unknown"
        group = next((sorted(group)[0] for group in GROUPS if project in group), project)
        rows.append({
            "id": item["id"], "project": project, "capture": str(capture.relative_to(ROOT)),
            "receipt": str(path.relative_to(ROOT)), "raw_sha256": item["sha256"],
            "command_path": item["command_path"], "reserved_split": assignments[project],
            "candidate_leakage_group": group, "source_family": family,
            "annotation_status": "audited" if item["id"] in audited else "pending",
        })
    if len(rows) != len({row["project"] for row in rows}) or len(rows) != len(assignments):
        raise ValueError("Capture coverage differs from the project reservation")
    groups = {}
    hashes = {}
    for row in rows:
        groups.setdefault(row["candidate_leakage_group"], []).append(row)
        hashes.setdefault(row["raw_sha256"], []).append(row)
    crossing = {
        name: [r["project"] for r in members] for name, members in groups.items()
        if len({r["reserved_split"] for r in members}) > 1
    }
    duplicates = [[r["project"] for r in members] for members in hashes.values() if len(members) > 1]
    similarity_flags = []
    for left, right in combinations(rows, 2):
        a, b = shingles[left["project"]], shingles[right["project"]]
        overlap = len(a & b)
        if overlap < 20:
            continue
        score = overlap / len(a | b)
        containment = overlap / min(len(a), len(b))
        if score >= 0.5 or containment >= 0.8:
            similarity_flags.append({
                "projects": [left["project"], right["project"]],
                "jaccard": round(score, 4), "containment": round(containment, 4),
                "cross_split": left["reserved_split"] != right["reserved_split"],
            })
    pending = {split: sorted(row["id"] for row in rows
                            if row["reserved_split"] == split and row["annotation_status"] == "pending")
               for split in ("dev", "train", "familiar_test", "cobra_test", "clap_test")}
    print(json.dumps({
        "version": 1, "frozen": False, "projects": rows,
        "cross_split_candidate_groups": crossing, "exact_capture_duplicates": duplicates,
        "similarity_review_queue": similarity_flags,
        "primary_annotation_queue": pending,
    }, indent=2))


if __name__ == "__main__":
    main()
