"""Validated public projection of legacy content and the pinned research bundle."""

from copy import deepcopy
from datetime import date
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
CATEGORY_POLICY = (
    "Categories group entries by topical relevance, including risks, context and monitoring. "
    "Membership is not evidence of benefit or a recommendation. "
    "An entry can appear in more than one category; category totals must not be added together."
)


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


def classify_categories(root, entries):
    definitions = read_json(root / "categories.json")
    classification = read_json(root / "research/category-membership.json")
    require(isinstance(classification, dict) and classification.get("schemaVersion") == 1,
            "category membership", "use schema version 1 for the topic classification")
    descriptions = classification.get("descriptions")
    require(isinstance(descriptions, dict) and descriptions.keys() == definitions.keys(),
            "category membership", "provide a description for each existing category")
    require(all(isinstance(text, str) and text.strip() for text in descriptions.values()),
            "category membership", "category descriptions must be non-empty text")
    memberships = classification.get("memberships")
    imported = {key for key in entries if key.startswith("library:")}
    require(isinstance(memberships, dict) and memberships.keys() == imported,
            "category membership", "classify every additional entry exactly once; do not override legacy memberships")
    for key, entry in entries.items():
        categories = memberships[key] if key in imported else entry["categories"]
        require(isinstance(categories, list) and categories
                and all(isinstance(category, str) and category in definitions for category in categories),
                key, "assign at least one existing topic category")
        require(len(categories) == len(set(categories)),
                key, "remove duplicate topic memberships")
        entry["categories"] = list(categories)
    return {
        slug: {
            "name": definition["name"], "summary": descriptions[slug],
            "members": sorted(
                (key for key, entry in entries.items() if slug in entry["categories"]),
                key=lambda key: (entries[key]["title"].casefold(), key),
            ),
        }
        for slug, definition in definitions.items()
    }


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
    publication = read_json(root / "research/publication-review.json")
    require(isinstance(publication, dict) and publication.get("schemaVersion") == 2,
            "publication review", "record a complete suitability review before building")
    require(publication.get("sourceCommit") == SOURCE_COMMIT,
            "publication review", "source commit mismatch; review the pinned source")
    require(publication.get("result") == "historical-publication-suitable-with-limitations"
            and publication.get("clinicalVerification") == "not-performed",
            "publication review", "only historical-reference publication is approved")
    try:
        date.fromisoformat(publication.get("checkedOn", ""))
    except (TypeError, ValueError) as error:
        raise ValueError("publication review: record a valid ISO 8601 review date") from error
    entry_reviews = publication.get("entryReviews")
    require(isinstance(entry_reviews, dict) and entry_reviews.keys() == evidence.keys(),
            "publication review", "every source ID needs exactly one suitability disposition")
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
        review = entry_reviews[source_id]
        require(isinstance(review, dict) and type(review.get("protocolCount")) is int
                and review["protocolCount"] == len(data.get("protocols", [])),
                source_id, "publication review study coverage mismatch")
        community_review = review.get("community")
        require(isinstance(community_review, list)
                and len(community_review) == len(data.get("community", [])),
                source_id, "publication review community coverage mismatch")
        for index, check in enumerate(community_review):
            require(isinstance(check, dict), source_id, "invalid community review")
            require(check.get("origin") == f"evidence.json#/{source_id}/community/{index}"
                    and check.get("url") == data["community"][index]["source"]["url"],
                    source_id, "community review must match the original claim and citation")
            require(check.get("suitability") == "historical-reference-only"
                    and check.get("result") in {
                        "bounded-description-supported", "unverified-historical-account",
                        "disputed-support", "partial-match-unverified", "inconsistent-units-and-route",
                        "formulation-context-limited", "unit-interpretation-unverified",
                        "population-and-route-limited",
                    }
                    and all(isinstance(check.get(field), str) and check[field].strip()
                            for field in ("claimMatch", "population")),
                    source_id, "community review cannot certify a medical regimen")
        require(isinstance(review.get("notices"), list)
                and all(isinstance(note, str) and note.strip() for note in review["notices"]),
                source_id, "publication notices must be explicit text")
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
            "publicationReview": {
                "checkedOn": publication["checkedOn"], "status": "historical-reference-only",
                "clinicalVerification": "not-performed", "notices": deepcopy(review["notices"]),
                "community": [
                    {field: check[field] for field in
                     ("origin", "url", "claimMatch", "population", "suitability", "result")}
                    for check in community_review
                ],
            },
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
    categories = classify_categories(root, entries)
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
    availability_report = read_json(root / "research/citations-live-checks.json")
    require(isinstance(availability_report, dict)
            and availability_report.get("sourceCommit") == SOURCE_COMMIT
            and availability_report.get("checkedOn") == publication["checkedOn"]
            and isinstance(availability_report.get("checks"), list),
            "source availability", "record dated checks for this publication review")
    source_urls = {occurrence["url"] for source in sources.values()
                   for occurrence in source["occurrences"]}
    availability = {}
    for check in availability_report["checks"]:
        require(isinstance(check, dict) and check.get("url") in source_urls,
                "source availability", "unexpected citation URL")
        url = check["url"]
        require(url not in availability, url, "duplicate availability record")
        require(check.get("availability") in {
                    "retrieved-html", "retrieved-non-html", "http-error", "request-failed",
                    "response-limit-exceeded", "possible-access-barrier",
                    "circular-provenance-not-independently-retrieved",
                }
                and check.get("publisherContentStored") is False
                and isinstance(check.get("checkedAt"), str)
                and check["checkedAt"].startswith(publication["checkedOn"] + "T"),
                url, "invalid or mismatched source availability check")
        availability[url] = {
            "checkedOn": publication["checkedOn"], "status": check["availability"],
        }
        if "httpStatus" in check:
            require(type(check["httpStatus"]) is int and 100 <= check["httpStatus"] <= 599,
                    url, "invalid HTTP status in availability check")
            availability[url]["httpStatus"] = check["httpStatus"]
    require(availability.keys() == source_urls,
            "source availability", "every citation URL needs exactly one dated check")
    return {
        "schemaVersion": 1, "entries": entries, "sources": sources,
        "categories": categories, "categoryPolicy": CATEGORY_POLICY,
        "sourceAvailability": availability, "sourceCounts": counts,
        "stackConflicts": mapping["stackConflicts"], "sourceCommit": SOURCE_COMMIT,
        "reviewState": "historical-not-reverified",
        "publicationReview": {
            "checkedOn": publication["checkedOn"], "status": "historical-reference-only",
            "clinicalVerification": "not-performed",
        },
        "publication": (
            f"Historical-reference publication suitability checked {publication['checkedOn']}; "
            "not clinical, regulatory, efficacy, safety or dose verification. "
            "Unverified accounts and source limitations remain explicit."
        ),
    }
