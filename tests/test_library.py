import copy
import json
from pathlib import Path
import unittest

import library


ROOT = Path(__file__).resolve().parents[1]


class LibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogue = library.load_library(ROOT)

    def test_every_source_record_has_one_explicit_disposition(self):
        entries = self.catalogue["entries"]
        source_ids = [
            research["id"] for entry in entries.values()
            for research in entry["research"]
        ]
        self.assertEqual(len(source_ids), 210)
        self.assertEqual(len(set(source_ids)), 210)
        self.assertEqual(len(entries), 245)
        for slug in json.loads((ROOT / "peptides.json").read_text()):
            self.assertEqual(entries["peptide:" + slug]["path"], f"/peptides/{slug}.html")

    def test_aliases_cross_kinds_and_variants_are_explicit(self):
        entries = self.catalogue["entries"]
        self.assertEqual(entries["peptide:epithalon"]["research"][0]["title"], "Epitalon")
        self.assertEqual(entries["peptide:hgh-somatropin"]["kind"], "medication-hormone")
        self.assertTrue(entries["library:peptide-tb-500"]["related"])
        self.assertTrue(entries["library:peptide-kisspeptin-10"]["related"])
        blend = entries["library:peptide-cjc-ipamorelin-blend"]
        self.assertIn("peptide:ipamorelin", blend["related"])
        self.assertNotEqual(blend["path"], "/stacks/cjc-1295-ipamorelin.html")

    def test_research_preserves_population_empty_findings_and_conflicts(self):
        entries = self.catalogue["entries"]
        bpc = entries["peptide:bpc-157"]
        self.assertTrue(bpc["conflicts"])
        self.assertEqual(bpc["research"][0]["pk"]["lowerHours"], 4)
        self.assertIn("rats", bpc["research"][0]["protocols"][0]["population"])
        self.assertTrue(bpc["research"][0]["protocols"][0]["origins"])
        empty = entries["library:medication-paracetamol"]["research"][0]["communityFinding"]
        self.assertEqual(empty["status"], "no-verified-description")
        self.assertEqual(empty["checkedOn"], "2026-10-06")
        for entry in entries.values():
            for research in entry["research"]:
                self.assertNotIn("template", research)
                self.assertNotIn("typicalDoseValue", research)
                self.assertEqual(research["reviewState"], "historical-not-reverified")

    def test_sources_deduplicate_identity_without_losing_occurrences(self):
        sources = self.catalogue["sources"]
        source = sources["pmid:42542926"]
        self.assertGreater(len(source["occurrences"]), 1)
        self.assertTrue(all("origin" in occurrence for occurrence in source["occurrences"]))
        circular = [
            occurrence for source in sources.values()
            for occurrence in source["occurrences"] if occurrence["circular"]
        ]
        self.assertGreaterEqual(len(circular), 30)
        self.assertEqual(self.catalogue["sourceCounts"]["protocols"], 270)
        self.assertEqual(self.catalogue["sourceCounts"]["community"], 163)

    def test_exact_claim_deduplication_keeps_different_populations(self):
        first = {"population": "Mice", "regimen": "Reported", "source": {"url": "https://example.org"}}
        second = {**first, "population": "Adults"}
        claims = library.deduplicate_claims([first, first, second], "fixture")
        self.assertEqual(len(claims), 2)
        self.assertEqual(claims[0]["origins"], ["fixture/0", "fixture/1"])
        self.assertEqual(claims[1]["population"], "Adults")

    def test_every_canonical_field_and_claim_origin_survives_projection(self):
        raw = json.loads((ROOT / "research/biometra/evidence.json").read_text())
        ledger = json.loads((ROOT / "research/biometra/community-research.json").read_text())["entries"]
        authored = {entry["id"]: entry for entry in json.loads(
            (ROOT / "research/biometra/audit/catalogue-authored.json").read_text()
        )}
        projected = {
            research["id"]: research for entry in self.catalogue["entries"].values()
            for research in entry["research"]
        }
        for key, evidence in raw.items():
            public = projected[key]
            with self.subTest(source_id=key):
                for field in ("evidenceTier", "evidenceSummary", "verdict", "links"):
                    self.assertEqual(public[field], evidence[field])
                for field in ("title", "summary", "uncertainty"):
                    self.assertEqual(public[field], authored[key][field])
                self.assertEqual(public["originalLinks"], authored[key]["officialLinks"])
                self.assertEqual(public["communityFinding"], ledger.get(key))
                for field in ("protocols", "community"):
                    restored = {}
                    for claim in public[field]:
                        for origin in claim["origins"]:
                            restored[int(origin.rsplit("/", 1)[1])] = {
                                name: value for name, value in claim.items() if name != "origins"
                            }
                    self.assertEqual([restored[i] for i in sorted(restored)], evidence.get(field, []))

    def test_incomplete_ambiguous_or_unsafe_mapping_is_rejected(self):
        original = json.loads((ROOT / "research/mapping.json").read_text())
        for mutation in ("missing", "duplicate", "unsafe", "unrelated"):
            mapping = copy.deepcopy(original)
            if mutation == "missing":
                mapping["newEntities"]["context"].remove("sleep")
            elif mutation == "duplicate":
                mapping["newEntities"]["peptide"].append("bpc-157")
            elif mutation == "unsafe":
                mapping["legacyMatches"]["catalog:peptide:bpc-157"] = "../outside"
            else:
                mapping["variants"]["catalog:peptide:tb-500"]["related"] = ["peptide:missing"]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                library.load_library(ROOT, mapping=mapping)


if __name__ == "__main__":
    unittest.main()
