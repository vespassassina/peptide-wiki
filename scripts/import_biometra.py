#!/usr/bin/env python3
"""Preserve pinned, authored Biometra research without changing the public wiki."""

import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "adc7684614f9439b41d91a3312b62e7982c7e20e"
DOMAIN = "HealthAgentKit/Sources/HealthAgentDomain"
EVIDENCE = "scripts/evidence/evidence.json"
LEDGER = "scripts/evidence/community-research.json"
AUDIT = "docs/research/B-82"
ACCESSOR = b"private static let authoredEntries"
PINNED_HASHES = {
    EVIDENCE: "8acf37f1080a1cb0631c8ce61bdcb0be61f369aafd4344f36f031e2c7859d7d6",
    LEDGER: "924aea0251ab76038406e699fe9d7811ea2633c32cd240a06fce7b36c7e1cec9",
    f"{DOMAIN}/LibraryCatalog.swift": "9ecdd90f446a97124d0055e07422c3312c57c525da6973aa1f3727038f43c36f",
}
AUDIT_ROLES = {
    "README.md": "reuse-instructions",
    "catalogue-evidence.json": "dated-evidence-snapshot-not-current",
    "research-outcomes.json": "final-dated-outcome-ledger",
    "candidate-research.json": "intermediate-proposals-not-approved",
    "working-editorial-review.json": "intermediate-review-including-rejections",
    "existing-description-review.json": "review-notes-not-article-content",
    "publication-overrides.json": "historical-final-editorial-overrides",
    "source-fetch-index.json": "retrieval-metadata-not-claim-verification",
    "offline-inventory.json": "historical-inventory-absent-caches-not-imported",
    "fetch_sources.py": "historical-helper-not-executed",
}
EXPECTED_COUNTS = {
    "entries": 210, "links": 543, "protocols": 270, "community": 163,
    "verdicts": 210, "ledgerEntries": 130, "verifiedDescription": 59,
    "noVerifiedDescription": 71, "circularWikiLinks": 30,
}
TIERS = {"regulatory", "systematic-review", "clinical-study", "preclinical", "reference"}
KINDS = {
    "peptide", "medication-hormone", "supplement", "food-protocol",
    "exercise-plan", "recovery-practice", "context", "lab-marker",
}


class ImportFailure(ValueError):
    """An invalid input must not produce a successful or partial import."""


def require(condition, location, reason):
    if not condition:
        raise ImportFailure(f"{location}: {reason}. Correct the input and rerun; nothing was replaced")


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def load_json(raw, location):
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, location, f"duplicate JSON key {key!r}")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ImportFailure(f"{location}: non-finite JSON number {value}; use a valid JSON value")

    try:
        return json.loads(raw, object_pairs_hook=object_pairs, parse_constant=invalid_constant)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ImportFailure(f"{location}: invalid UTF-8 JSON: {error}; correct the source") from error


def relative_path(value):
    path = PurePosixPath(value)
    require(
        bool(path.parts) and not path.is_absolute() and ".." not in path.parts
        and "\\" not in value and str(path) == value,
        value, "expected a normal relative path without traversal",
    )
    return path


def read_source_file(root, relative):
    path = relative_path(relative)
    full = root
    for component in path.parts:
        full /= component
        require(not full.is_symlink(), relative, "symlinked source files/directories are not allowed")
    require(full.is_file(), relative, "required source file is missing")
    return full.read_bytes()


def run(command, *, cwd=None):
    try:
        return subprocess.run(command, cwd=cwd, capture_output=True, check=True).stdout
    except FileNotFoundError as error:
        raise ImportFailure(f"{command[0]} is missing; install the migration toolchain before retrying") from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode("utf-8", errors="replace").strip()
        raise ImportFailure(f"{command[0]} failed: {detail}; no bundle was replaced") from error


def source_files(root):
    head = run(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()
    require(head == SOURCE_COMMIT, "source HEAD", f"expected pinned commit {SOURCE_COMMIT}, got {head}")
    paths = run([
        "git", "ls-tree", "-r", "--name-only", SOURCE_COMMIT, "--",
        DOMAIN, EVIDENCE, LEDGER, AUDIT,
    ], cwd=root).decode().splitlines()
    domain_paths = sorted(p for p in paths if p.startswith(DOMAIN + "/") and p.endswith(".swift"))
    audit_paths = sorted(p for p in paths if p.startswith(AUDIT + "/"))
    require(
        set(audit_paths) == {f"{AUDIT}/{name}" for name in AUDIT_ROLES},
        AUDIT, "tracked audit inventory differs from the reviewed allowlist",
    )
    require(domain_paths, DOMAIN, "no domain Swift compilation inputs found")
    selected = domain_paths + [EVIDENCE, LEDGER] + audit_paths
    result = {}
    for path in selected:
        raw = read_source_file(root, path)
        pinned = run(["git", "show", f"{SOURCE_COMMIT}:{path}"], cwd=root)
        require(raw == pinned, path, "working file differs from the pinned commit")
        if path in PINNED_HASHES:
            require(sha256(raw) == PINNED_HASHES[path], path, "pinned SHA-256 mismatch")
        result[path] = raw
    return result


def export_catalogue(sources):
    original = sources.get("LibraryCatalog.swift", b"")
    require(original.count(ACCESSOR) == 1, "LibraryCatalog.swift", "expected exactly one private authoredEntries accessor")
    with tempfile.TemporaryDirectory(prefix="biohacker-export-") as directory:
        scratch = Path(directory)
        inputs = []
        for name, raw in sorted(sources.items()):
            relative_path(name)
            require("/" not in name and name.endswith(".swift"), name, "expected a domain Swift filename")
            if name == "LibraryCatalog.swift":
                raw = raw.replace(ACCESSOR, b"static let authoredEntries", 1)
            path = scratch / name
            path.write_bytes(raw)
            inputs.append(str(path))
        exporter = scratch / "ExportBiometra.swift"
        exporter.write_bytes((ROOT / "scripts/export_biometra.swift").read_bytes())
        executable = scratch / "export-biometra"
        run([
            "swiftc", "-swift-version", "6", "-parse-as-library",
            "-module-cache-path", str(scratch / "module-cache"),
            *inputs, str(exporter), "-o", str(executable),
        ])
        raw = run([str(executable)])
        load_json(raw, "authored catalogue export")
        return raw


def object_fields(value, required, optional, location):
    require(isinstance(value, dict), location, "expected an object")
    missing = required - value.keys()
    unknown = value.keys() - required - optional
    require(not missing, location, f"missing fields {sorted(missing)}")
    require(not unknown, location, f"unreviewed fields {sorted(unknown)}")


def text(value, location):
    require(isinstance(value, str) and bool(value.strip()), location, "expected non-empty text")


def identifier(value, location):
    require(
        isinstance(value, str) and re.fullmatch(r"catalog:[a-z0-9-]+:[a-z0-9-]+", value),
        location, f"invalid catalogue id {value!r}",
    )


def url(value, location):
    text(value, location)
    try:
        parsed = urlsplit(value)
        parsed.port
    except ValueError as error:
        raise ImportFailure(f"{location}: invalid URL: {error}; correct the source") from error
    require(
        parsed.scheme in {"https", "http"} and bool(parsed.hostname)
        and parsed.username is None and parsed.password is None
        and not any(character.isspace() or ord(character) < 32 for character in value),
        location, "expected an HTTP(S) URL without credentials or whitespace",
    )


def link(value, location):
    object_fields(value, {"title", "url"}, {"author"}, location)
    text(value["title"], location + ".title")
    url(value["url"], location + ".url")
    if value.get("author") is not None:
        text(value["author"], location + ".author")


def array(value, location):
    require(isinstance(value, list), location, "expected an array")
    return value


def validate_template(value, ids, location):
    require(isinstance(value, dict), location, "expected a template object")
    if "halfLife" in value:
        half_life = value["halfLife"]
        object_fields(half_life, {"hours"}, {"lowerHours", "upperHours", "source"}, location + ".halfLife")
        for key in ("hours", "lowerHours", "upperHours"):
            if key in half_life:
                require(
                    type(half_life[key]) in (int, float) and half_life[key] > 0,
                    location + ".halfLife." + key, "expected a positive number",
                )
        if "lowerHours" in half_life or "upperHours" in half_life:
            require(
                "lowerHours" in half_life and "upperHours" in half_life
                and half_life["lowerHours"] <= half_life["hours"] <= half_life["upperHours"],
                location + ".halfLife", "range must bracket the reported half-life",
            )
    if "blend" in value:
        object_fields(value["blend"], {"components"}, set(), location + ".blend")
        for component in array(value["blend"].get("components"), location + ".blend.components"):
            require(isinstance(component, dict), location + ".blend", "expected a component object")
            related = component.get("libraryEntryId")
            require(
                related is None or (isinstance(related, str) and related in ids),
                location + ".blend.libraryEntryId",
                f"unresolved component {related}",
            )


def validate_catalogue(catalogue, evidence):
    entries = array(catalogue, "catalogue")
    ids = []
    for entry in entries:
        object_fields(
            entry,
            {"id", "kind", "title", "summary", "evidenceTier", "uncertainty",
             "officialLinks", "provenance", "researchProtocols", "communityProtocols"},
            {"template", "evidenceSummary", "verdict"}, "catalogue entry",
        )
        identifier(entry["id"], "catalogue.id")
        require(entry["id"] not in ids, "catalogue", f"duplicate id {entry['id']}")
        ids.append(entry["id"])
        for field in ("title", "summary", "uncertainty"):
            text(entry[field], f"{entry['id']}.{field}")
        require(isinstance(entry["kind"], str) and entry["kind"] in KINDS, entry["id"], "unknown item kind")
        require(isinstance(entry["evidenceTier"], str) and entry["evidenceTier"] in TIERS, entry["id"], "unknown authored evidence tier")
        require(entry["provenance"] == "built-in", entry["id"], "only built-in authored records are permitted")
        for source in array(entry["officialLinks"], entry["id"] + ".officialLinks"):
            link(source, entry["id"] + ".officialLinks")
        for field in ("researchProtocols", "communityProtocols"):
            require(entry[field] == [], entry["id"] + "." + field, "authored export unexpectedly contains overlaid research")
    require(isinstance(evidence, dict), "evidence", "expected an ID-keyed object")
    require(set(ids) == evidence.keys(), "catalogue/evidence", "ID parity mismatch")
    for entry in entries:
        if "template" in entry:
            validate_template(entry["template"], set(ids), entry["id"] + ".template")


def validate_evidence(evidence):
    counts = Counter(entries=len(evidence))
    for key, entry in evidence.items():
        identifier(key, "evidence key")
        object_fields(
            entry, {"id", "evidenceTier", "evidenceSummary", "links", "verdict"},
            {"changes", "protocols", "community"}, key,
        )
        require(entry["id"] == key, key + ".id", "key and record ID differ")
        require(isinstance(entry["evidenceTier"], str) and entry["evidenceTier"] in TIERS, key, "unknown evidence tier")
        text(entry["evidenceSummary"], key + ".evidenceSummary")
        for source in array(entry["links"], key + ".links"):
            link(source, key + ".links")
            counts["links"] += 1
            if source["url"].startswith("https://vespassassina.github.io/peptide-wiki/"):
                counts["circularWikiLinks"] += 1
        for protocol in array(entry.get("protocols", []), key + ".protocols"):
            location = key + ".protocols"
            object_fields(protocol, {"population", "regimen", "duration", "outcome", "source"}, set(), location)
            for field in ("population", "regimen", "duration", "outcome"):
                text(protocol[field], location + "." + field)
            link(protocol["source"], location + ".source")
            counts["protocols"] += 1
        for community in array(entry.get("community", []), key + ".community"):
            object_fields(community, {"description", "source"}, set(), key + ".community")
            text(community["description"], key + ".community.description")
            link(community["source"], key + ".community.source")
            counts["community"] += 1
        verdict = entry["verdict"]
        object_fields(verdict, {"benefits", "risks", "bottomLine"}, {"approvalStatus"}, key + ".verdict")
        for field in ("benefits", "risks"):
            for item in array(verdict[field], key + ".verdict." + field):
                text(item, key + ".verdict." + field)
        text(verdict["bottomLine"], key + ".verdict.bottomLine")
        if "approvalStatus" in verdict:
            text(verdict["approvalStatus"], key + ".verdict.approvalStatus")
        counts["verdicts"] += 1
    return counts


def validate_ledger(ledger, evidence, counts):
    object_fields(ledger, {"scope", "interpretation", "entries"}, set(), "ledger")
    text(ledger["scope"], "ledger.scope")
    text(ledger["interpretation"], "ledger.interpretation")
    require(isinstance(ledger["entries"], dict), "ledger.entries", "expected an ID-keyed object")
    for key, entry in ledger["entries"].items():
        require(key in evidence, key, "ledger ID missing from evidence")
        object_fields(entry, {"checkedOn", "status", "notes", "checks"}, {"community"}, key + ".ledger")
        try:
            checked = date.fromisoformat(entry["checkedOn"])
        except (TypeError, ValueError) as error:
            raise ImportFailure(f"{key}.checkedOn: invalid ISO date; correct the ledger") from error
        require(checked.isoformat() == entry["checkedOn"], key + ".checkedOn", "expected YYYY-MM-DD")
        text(entry["notes"], key + ".ledger.notes")
        require(
            isinstance(entry["status"], str) and entry["status"] in {"verified-description", "no-verified-description"},
            key + ".ledger.status", "unknown final research outcome",
        )
        checks = array(entry["checks"], key + ".checks")
        require(bool(checks), key + ".checks", "final outcome needs recorded checks")
        for check in checks:
            object_fields(check, {"url", "outcome", "reason"}, set(), key + ".checks")
            url(check["url"], key + ".checks.url")
            text(check["outcome"], key + ".checks.outcome")
            text(check["reason"], key + ".checks.reason")
        if "community" in entry:
            require(entry["community"] == evidence[key].get("community", []), key + ".ledger.community", "final description differs from canonical evidence")
        if entry["status"] == "no-verified-description":
            require(not evidence[key].get("community"), key, "empty outcome has a canonical community description")
        else:
            require(bool(evidence[key].get("community")), key, "verified outcome has no canonical description")
        counts["ledgerEntries"] += 1
        field = "verifiedDescription" if entry["status"] == "verified-description" else "noVerifiedDescription"
        counts[field] += 1


def validate_research(catalogue, evidence, ledger):
    validate_catalogue(catalogue, evidence)
    counts = validate_evidence(evidence)
    validate_ledger(ledger, evidence, counts)
    return {key: counts[key] for key in EXPECTED_COUNTS}


def validate_expected_counts(counts):
    for key, expected in EXPECTED_COUNTS.items():
        require(counts[key] == expected, "reconciliation." + key, f"expected {expected}, got {counts[key]}")


def prepare_bundle(sources, catalogue_raw):
    catalogue = load_json(catalogue_raw, "authored catalogue")
    evidence = load_json(sources[EVIDENCE], EVIDENCE)
    ledger = load_json(sources[LEDGER], LEDGER)
    counts = validate_research(catalogue, evidence, ledger)
    validate_expected_counts(counts)
    require(
        sources[LEDGER] == sources[f"{AUDIT}/research-outcomes.json"],
        LEDGER, "canonical and archived final ledger bytes differ",
    )
    for path, raw in sources.items():
        if path.startswith(AUDIT + "/") and path.endswith(".json"):
            load_json(raw, path)
    files = {
        "evidence.json": sources[EVIDENCE],
        "community-research.json": sources[LEDGER],
        "audit/catalogue-authored.json": catalogue_raw,
        "audit/source/LibraryCatalog.swift": sources[f"{DOMAIN}/LibraryCatalog.swift"],
    }
    records = [
        {"sourcePath": EVIDENCE, "targetPath": "evidence.json", "role": "canonical-evidence"},
        {"sourcePath": LEDGER, "targetPath": "community-research.json", "role": "canonical-final-outcome-ledger"},
        {"sourcePath": f"{DOMAIN}/LibraryCatalog.swift", "targetPath": "audit/source/LibraryCatalog.swift", "role": "original-authored-source"},
    ]
    for name, role in sorted(AUDIT_ROLES.items()):
        source, target = f"{AUDIT}/{name}", f"audit/B-82/{name}"
        files[target] = sources[source]
        records.append({"sourcePath": source, "targetPath": target, "role": role})
    for record in records:
        record["sha256"] = sha256(files[record["targetPath"]])
        record["publication"] = "not-deployed"
    exporter = (ROOT / "scripts/export_biometra.swift").read_bytes()
    manifest = {
        "schemaVersion": 1,
        "sourceRepository": "vespassassina/BiohackerAssistant",
        "sourceCommit": SOURCE_COMMIT,
        "counts": counts,
        "files": records,
        "authoredExport": {
            "targetPath": "audit/catalogue-authored.json",
            "sha256": sha256(catalogue_raw),
            "records": len(catalogue),
            "roundTrip": "Every authored entry, including templates, PK ranges and blends, compared equal after Codable encode/decode.",
            "publication": "not-deployed",
        },
        "exporter": {
            "version": 1,
            "sha256": sha256(exporter),
            "sourceTransformation": "In a scratch copy only, replace the single 'private static let authoredEntries' with 'static let authoredEntries'. Encode authoredEntries, not builtInEntries.",
            "canonicalisation": "Sort JSON object keys and the template.typicalRecurrence.weekdays._0 integer Set only; decode canonical bytes and compare every complete entry to the authored value.",
            "compileInputs": [
                {"sourcePath": path, "sha256": sha256(raw),
                 "role": "generated-compilation-dependency-not-evidence" if path.endswith("/LibraryCatalogEvidence.swift") else "domain-compilation-input"}
                for path, raw in sorted(sources.items()) if path.startswith(DOMAIN + "/")
            ],
        },
        "policy": {
            "publicOutput": "No bundle file is deployed in Sprint 1. Future public projections require explicit field allowlists.",
            "templates": "Archive only; never recommendations, calculator autofill or public template objects.",
            "audit": "Intermediate/rejected drafts and dated snapshots are not accepted article content.",
            "sourceChecks": "Historical checks remain historical. No fresh verification or publication permission is conferred by migration.",
            "circularProvenance": "Source-to-wiki backlinks are preserved but are not independent corroboration.",
            "excluded": ["ignored/untracked files", "local-only archives", "publisher HTML/text caches and excerpts", "private health/store data", "credentials"],
            "archiveReview": "Only reviewed, pinned tracked B-82 files; cached textFile/archive paths are historical references, not imported file dependencies.",
        },
    }
    files["manifest.json"] = json_bytes(manifest)
    return files, counts


def persist_bundle(destination, files):
    for name, raw in files.items():
        relative_path(name)
        require(isinstance(raw, bytes), name, "expected validated file bytes")
    for ancestor in (destination, *destination.parents):
        require(not ancestor.is_symlink(), str(ancestor), "symlinked destination is not allowed")
    if destination.exists():
        require(destination.is_dir(), str(destination), "existing destination is not a directory")
        actual = {}
        for path in destination.rglob("*"):
            require(not path.is_symlink(), str(path), "existing bundle contains a symlink")
            if path.is_file():
                actual[str(path.relative_to(destination))] = path.read_bytes()
        require(actual == files, str(destination), "existing bundle differs; review it rather than overwrite it")
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".biometra-import-", dir=destination.parent) as directory:
        stage = Path(directory) / "bundle"
        stage.mkdir()
        for name, raw in files.items():
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        require(not destination.exists(), str(destination), "destination appeared during validation")
        stage.rename(destination)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Approved read-only worktree at the pinned commit")
    parser.add_argument("--write", action="store_true", help="Persist the fully validated bundle; default is a read-only preview")
    args = parser.parse_args()
    try:
        sources = source_files(args.source)
        domain_sources = {
            PurePosixPath(path).name: raw for path, raw in sources.items()
            if path.startswith(DOMAIN + "/")
        }
        catalogue_raw = export_catalogue(domain_sources)
        files, counts = prepare_bundle(sources, catalogue_raw)
        # Re-read after compilation so concurrent source changes cannot escape the pin check.
        require(source_files(args.source) == sources, "source worktree", "inputs changed during export")
        if args.write:
            changed = persist_bundle(ROOT / "research/biometra", files)
            action = "Imported" if changed else "Already identical"
        else:
            action = "Validated preview; no repository files written"
        print(f"{action}: {json.dumps(counts, sort_keys=True)}")
    except (ImportFailure, OSError) as error:
        parser.exit(1, f"Import failed: {error}\n")


if __name__ == "__main__":
    main()
