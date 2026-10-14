"""Validated public projection of legacy content and the pinned research bundle."""

from copy import deepcopy
import hashlib
import json
import re
from urllib.parse import urlsplit

from scripts.import_biometra import (
    SOURCE_COMMIT, load_json, require, validate_expected_counts, validate_research,
)


KIND_LABELS = {
    "peptide": "Peptides",
    "medication-hormone": "Medications & hormones",
    "supplement": "Supplements",
    "food-protocol": "Food & fasting",
    "exercise-plan": "Exercise",
    "recovery-practice": "Recovery practices",
    "context": "Context & habits",
    "lab-marker": "Lab markers",
}
TIER_LABELS = {
    "regulatory": "Regulator / guideline",
    "systematic-review": "Systematic review",
    "clinical-study": "Clinical study",
    "preclinical": "Preclinical",
    "reference": "Reference only",
}


def read_json(path):
    return load_json(path.read_bytes(), str(path))


def deduplicate_claims(claims, origin):
    result, indexed = [], {}
    for index, claim in enumerate(claims):
        key = json.dumps(claim, sort_keys=True, ensure_ascii=False)
        if key not in indexed:
            indexed[key] = {**deepcopy(claim), "origins": []}
            result.append(indexed[key])
        indexed[key]["origins"].append(f"{origin}/{index}")
    return result


def citation_identity(url):
    parsed = urlsplit(url)
    if parsed.hostname == "pubmed.ncbi.nlm.nih.gov" and re.fullmatch(r"/\d+/?", parsed.path):
        return "pmid:" + parsed.path.strip("/")
    if parsed.hostname in {"doi.org", "dx.doi.org"}:
        return "doi:" + parsed.path.strip("/").lower()
    return url


def load_library(root, mapping=None):
    bundle = root / "research/biometra"
    manifest = read_json(bundle / "manifest.json")
    for record in manifest["files"] + [manifest["authoredExport"]]:
        raw = (bundle / record["targetPath"]).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == record["sha256"],
                record["targetPath"], "bundle hash differs from the pinned manifest")
    catalogue = read_json(bundle / "audit/catalogue-authored.json")
    evidence = read_json(bundle / "evidence.json")
    ledger = read_json(bundle / "community-research.json")
    counts = validate_research(catalogue, evidence, ledger)
    validate_expected_counts(counts)
    mapping = mapping if mapping is not None else read_json(root / "research/mapping.json")
    require(mapping["sourceCommit"] == SOURCE_COMMIT, "mapping", "source commit mismatch")
    legacy = read_json(root / "peptides.json")
    entries = {
        "peptide:" + slug: {
            "id": "peptide:" + slug, "path": f"/peptides/{slug}.html",
            "title": value["name"], "summary": value["tagline"],
            "aliases": list(value["aliases"]), "kind": "peptide",
            "categories": value["categories"], "legacy": deepcopy(value),
            "research": [], "related": ["peptide:" + s for s in value["related"]],
            "conflicts": deepcopy(mapping["conflicts"].get("peptide:" + slug, [])),
            "sourceRefs": [],
        }
        for slug, value in legacy.items()
    }
    assigned = {}
    for source_id, slug in mapping["legacyMatches"].items():
        require(slug in legacy, source_id, f"legacy match {slug!r} does not exist")
        assigned[source_id] = "peptide:" + slug
    for namespace, slugs in mapping["newEntities"].items():
        for slug in slugs:
            source_id = f"catalog:{namespace}:{slug}"
            require(source_id not in assigned, source_id, "duplicate mapping disposition")
            require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", namespace)
                    and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug),
                    source_id, "unsafe mapping route")
            assigned[source_id] = f"library:{namespace}-{slug}"
    require(assigned.keys() == evidence.keys(), "mapping", "every source ID needs exactly one explicit disposition")
    for authored in catalogue:
        source_id = authored["id"]
        target = assigned[source_id]
        if target not in entries:
            entries[target] = {
                "id": target, "path": f"/library/{target.split(':', 1)[1]}.html",
                "title": authored["title"], "summary": authored["summary"],
                "aliases": [], "kind": authored["kind"], "categories": [],
                "research": [], "related": [], "conflicts": [], "sourceRefs": [],
            }
        entry = entries[target]
        entry["kind"] = authored["kind"]
        if authored["title"] != entry["title"]:
            entry["aliases"].append(authored["title"])
        data = evidence[source_id]
        research = {
            "id": source_id, "title": authored["title"], "summary": authored["summary"],
            "uncertainty": authored["uncertainty"], "namespace": source_id.split(":")[1],
            "evidenceTier": data["evidenceTier"], "evidenceSummary": data["evidenceSummary"],
            "verdict": deepcopy(data["verdict"]), "originalLinks": deepcopy(authored["officialLinks"]),
            "links": deepcopy(data["links"]),
            "protocols": deduplicate_claims(data.get("protocols", []), f"evidence.json#/{source_id}/protocols"),
            "community": deduplicate_claims(data.get("community", []), f"evidence.json#/{source_id}/community"),
            "communityFinding": deepcopy(ledger["entries"].get(source_id)),
            "reviewState": "historical-not-reverified", "sourceCommit": SOURCE_COMMIT,
        }
        template = authored.get("template", {})
        if "halfLife" in template:
            research["pk"] = deepcopy(template["halfLife"])
        for component in template.get("blend", {}).get("components", []):
            if component.get("libraryEntryId"):
                entry["related"].append(assigned[component["libraryEntryId"]])
        variant = mapping["variants"].get(source_id)
        if variant:
            entry["related"] += variant["related"]
            entry["conflicts"].append({
                "status": "identity-uncertain", "text": variant["reason"],
                "origins": [f"catalogue-authored.json#{source_id}", "research/mapping.json"],
            })
            for related in variant["related"]:
                require(related in entries, source_id, f"unresolved related identity {related}")
                entries[related]["related"].append(target)
        entry["research"].append(research)
    sources = {}

    def register(entry, source, origin):
        identity = citation_identity(source["url"])
        if identity not in sources:
            sources[identity] = {"id": identity, "occurrences": []}
        occurrence = {**deepcopy(source), "origin": origin,
                      "circular": source["url"].startswith("https://vespassassina.github.io/peptide-wiki/")}
        sources[identity]["occurrences"].append(occurrence)
        if entry is not None and identity not in entry["sourceRefs"]:
            entry["sourceRefs"].append(identity)

    for entry in entries.values():
        for index, source in enumerate(entry.get("legacy", {}).get("citations", [])):
            register(entry, {"title": source["title"], "url": source["pubmed_url"],
                             "authorsYear": source["authors_year"]},
                     f"peptides.json#/{entry['id'].split(':')[1]}/citations/{index}")
        for research in entry["research"]:
            for field in ("links", "originalLinks"):
                for index, source in enumerate(research[field]):
                    register(entry, source, f"{research['id']}/{field}/{index}")
            for field in ("protocols", "community"):
                for claim in research[field]:
                    for origin in claim["origins"]:
                        register(entry, claim["source"], origin + "/source")
        entry["related"] = sorted(set(entry["related"]))
        require(set(entry["related"]) <= entries.keys(), entry["id"], "unresolved related entity")
    for slug, stack in read_json(root / "stacks.json").items():
        for index, source in enumerate(stack["citations"]):
            register(None, {"title": source["title"], "url": source["pubmed_url"],
                            "authorsYear": source["authors_year"]},
                     f"stacks.json#/{slug}/citations/{index}")
    return {
        "schemaVersion": 1, "entries": entries, "sources": sources, "sourceCounts": counts,
        "stackConflicts": mapping["stackConflicts"], "sourceCommit": SOURCE_COMMIT,
        "reviewState": "historical-not-reverified",
        "publication": "Local migration only; fresh suitability/rights checks required before republication.",
    }
