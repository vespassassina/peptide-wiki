import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "research/biometra"
spec = importlib.util.spec_from_file_location(
    "bundle_importer", ROOT / "scripts/import_biometra.py"
)
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)


class ResearchBundleTests(unittest.TestCase):
    def test_all_preserved_files_match_the_manifest(self):
        manifest = json.loads((BUNDLE / "manifest.json").read_text())
        self.assertEqual(manifest["sourceCommit"], importer.SOURCE_COMMIT)
        records = manifest["files"] + [manifest["authoredExport"]]
        expected_paths = {"manifest.json"}
        for record in records:
            path = record["targetPath"]
            expected_paths.add(path)
            with self.subTest(path=path):
                raw = (BUNDLE / path).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), record["sha256"])
                self.assertEqual(record["publication"], "not-deployed")
        self.assertEqual(
            {str(p.relative_to(BUNDLE)) for p in BUNDLE.rglob("*") if p.is_file()},
            expected_paths,
        )
        self.assertNotIn("local-only", expected_paths)
        self.assertEqual(
            (BUNDLE / "community-research.json").read_bytes(),
            (BUNDLE / "audit/B-82/research-outcomes.json").read_bytes(),
        )

    def test_complete_research_counts_and_original_optional_metadata(self):
        catalogue = importer.load_json(
            (BUNDLE / "audit/catalogue-authored.json").read_bytes(), "catalogue"
        )
        evidence = importer.load_json((BUNDLE / "evidence.json").read_bytes(), "evidence")
        ledger = importer.load_json((BUNDLE / "community-research.json").read_bytes(), "ledger")
        counts = importer.validate_research(catalogue, evidence, ledger)
        self.assertEqual(counts, importer.EXPECTED_COUNTS)
        manifest = json.loads((BUNDLE / "manifest.json").read_text())
        self.assertEqual(counts, manifest["counts"])
        bodyweight = evidence["catalog:exercise:bodyweight"]["community"][0]["source"]
        self.assertIn("author", bodyweight)
        self.assertIsNone(bodyweight["author"])

    def test_hand_checked_examples_retain_uncertainty_conflicts_and_bounded_empty_findings(self):
        catalogue = {
            item["id"]: item
            for item in json.loads((BUNDLE / "audit/catalogue-authored.json").read_text())
        }
        evidence = json.loads((BUNDLE / "evidence.json").read_text())
        ledger = json.loads((BUNDLE / "community-research.json").read_text())
        bpc = catalogue["catalog:peptide:bpc-157"]
        self.assertEqual(bpc["template"]["halfLife"]["lowerHours"], 4)
        self.assertEqual(bpc["template"]["halfLife"]["upperHours"], 6)
        self.assertTrue(bpc["uncertainty"])
        self.assertTrue(any("ClinicalTrials.gov" in source["title"] for source in bpc["officialLinks"]))
        self.assertIn("rats", evidence[bpc["id"]]["protocols"][0]["population"])
        empty = ledger["entries"]["catalog:medication:paracetamol"]
        self.assertEqual(empty["checkedOn"], "2026-10-06")
        self.assertEqual(empty["status"], "no-verified-description")
        self.assertIn("does not establish", empty["notes"])
        self.assertTrue(evidence["catalog:context:sleep"]["community"])
        self.assertEqual(
            json.loads((BUNDLE / "audit/B-82/catalogue-evidence.json").read_text()).keys()
            <= evidence.keys(),
            True,
        )


if __name__ == "__main__":
    unittest.main()
