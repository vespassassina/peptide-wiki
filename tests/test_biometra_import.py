import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "import_biometra", ROOT / "scripts/import_biometra.py"
)
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)


def example_data():
    identifier = "catalog:context:test"
    link = {"title": "Study", "url": "https://example.org/study"}
    catalogue = [{
        "id": identifier, "kind": "context", "title": "Test",
        "summary": "Authored overview", "evidenceTier": "reference",
        "uncertainty": "Unknown", "officialLinks": [link], "provenance": "built-in",
        "researchProtocols": [], "communityProtocols": [],
        "template": {"usageNote": "Archived default", "suggestedLabAnalyteIds": []},
    }]
    evidence = {identifier: {
        "id": identifier, "evidenceTier": "reference", "evidenceSummary": "Research",
        "links": [link], "verdict": {
            "benefits": ["Unknown benefit"], "risks": ["Unknown risk"],
            "bottomLine": "Uncertain",
        },
        "protocols": [{
            "population": "Mice", "regimen": "Study intervention",
            "duration": "One week", "outcome": "Not significant", "source": link,
        }],
        "community": [],
    }}
    ledger = {
        "scope": "Fixture", "interpretation": "Bounded finding",
        "entries": {identifier: {
            "checkedOn": "2026-10-06", "status": "no-verified-description",
            "notes": "No suitable account verified",
            "checks": [{"url": link["url"], "outcome": "not-verified", "reason": "Unknown"}],
        }},
    }
    return catalogue, evidence, ledger


class ImportValidationTests(unittest.TestCase):
    def test_reconciliation_counts_original_occurrences(self):
        catalogue, evidence, ledger = example_data()
        evidence[catalogue[0]["id"]]["links"] *= 2
        counts = importer.validate_research(catalogue, evidence, ledger)
        self.assertEqual(counts["entries"], 1)
        self.assertEqual(counts["links"], 2)
        self.assertEqual(counts["protocols"], 1)
        self.assertEqual(counts["community"], 0)
        self.assertEqual(counts["noVerifiedDescription"], 1)

    def test_duplicate_keys_are_rejected(self):
        with self.assertRaisesRegex(importer.ImportFailure, "duplicate.*id"):
            importer.load_json(b'{"id":"a","id":"b"}', "fixture.json")

    def test_source_author_metadata_is_preserved(self):
        data = example_data()
        source = data[1]["catalog:context:test"]["links"][0]
        source["author"] = "Original researcher"
        importer.validate_research(*data)
        self.assertEqual(source["author"], "Original researcher")
        source["author"] = None
        importer.validate_research(*data)
        self.assertIn("author", source)
        self.assertIsNone(source["author"])

    def test_invalid_shapes_and_identity_fail_with_context(self):
        cases = []
        data = example_data()
        data[0].append(copy.deepcopy(data[0][0]))
        cases.append((data, "duplicate.*catalog:context:test"))
        data = example_data()
        data[1]["catalog:context:test"]["protocols"][0].pop("population")
        cases.append((data, "population"))
        data = example_data()
        data[1]["catalog:context:test"]["links"][0]["url"] = "javascript:alert(1)"
        cases.append((data, "url"))
        data = example_data()
        data[1]["catalog:context:test"]["extra"] = "Unmapped field"
        cases.append((data, "extra"))
        data = example_data()
        data[0][0]["id"] = "catalog:context:../../outside"
        cases.append((data, "id"))
        data = example_data()
        data[0][0]["template"]["blend"] = {
            "components": [{"libraryEntryId": "catalog:missing:entry"}]
        }
        cases.append((data, "catalog:missing:entry"))
        data = example_data()
        data[0][0]["template"]["blend"] = []
        cases.append((data, "blend"))
        data = example_data()
        data[1]["catalog:context:test"]["links"][0]["url"] = "https://[invalid"
        cases.append((data, "url"))
        data = example_data()
        data[0][0]["kind"] = []
        cases.append((data, "kind"))
        for data, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(importer.ImportFailure, message):
                    importer.validate_research(*data)

    def test_wrong_ledger_status_date_or_empty_outcome_is_rejected(self):
        for field, value in (
            ("status", "approved"),
            ("checkedOn", "yesterday"),
            ("checks", []),
        ):
            data = example_data()
            data[2]["entries"]["catalog:context:test"][field] = value
            with self.subTest(field=field):
                with self.assertRaises(importer.ImportFailure):
                    importer.validate_research(*data)

    def test_invalid_count_does_not_become_a_successful_import(self):
        counts = importer.validate_research(*example_data())
        with self.assertRaisesRegex(importer.ImportFailure, "entries.*210"):
            importer.validate_expected_counts(counts)

    def test_unsafe_source_paths_and_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "file.json").write_text("{}")
            (root / "link.json").symlink_to(root / "file.json")
            for path in ("../outside", "/absolute", "link.json"):
                with self.subTest(path=path):
                    with self.assertRaises(importer.ImportFailure):
                        importer.read_source_file(root, path)

    def test_existing_bundle_is_never_silently_overwritten(self):
        files = {"evidence.json": b"{}\n", "manifest.json": b"{}\n"}
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory).resolve() / "biometra"
            self.assertTrue(importer.persist_bundle(destination, files))
            self.assertFalse(importer.persist_bundle(destination, files))
            original = (destination / "evidence.json").read_bytes()
            with self.assertRaisesRegex(importer.ImportFailure, "differs"):
                importer.persist_bundle(destination, {**files, "evidence.json": b"[]"})
            self.assertEqual((destination / "evidence.json").read_bytes(), original)
            self.assertFalse((destination / "manifest.json").is_symlink())

    def test_partial_or_unsafe_bundle_never_creates_a_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory).resolve() / "biometra"
            with self.assertRaises(importer.ImportFailure):
                importer.persist_bundle(destination, {"../escape": b"bad"})
            self.assertFalse(destination.exists())


@unittest.skipUnless(shutil.which("swiftc"), "Swift is required only to test the migration exporter")
class CatalogueExportTests(unittest.TestCase):
    def test_export_keeps_authored_links_and_all_nested_values(self):
        source = b"""
import Foundation
struct Link: Codable, Equatable { var title: String; var url: String }
enum Recurrence: Codable, Equatable { case weekdays(Set<Int>) }
struct Template: Codable, Equatable {
    var typicalDoseValue: Double
    var halfLife: [String: Double]
    var blend: [String]
    var typicalRecurrence: Recurrence
}
struct LibraryCatalogEntry: Codable, Equatable {
    var id: String
    var officialLinks: [Link]
    var template: Template
}
enum LibraryCatalog {
    private static let authoredEntries = [
        LibraryCatalogEntry(
            id: "catalog:peptide:example",
            officialLinks: [Link(title: "Original", url: "https://example.org/authored")],
            template: Template(
                typicalDoseValue: 2.5,
                halfLife: ["hours": 5, "lowerHours": 4, "upperHours": 6],
                blend: ["catalog:peptide:other"],
                typicalRecurrence: .weekdays([5, 1, 3])
            )
        )
    ]
    static let builtInEntries: [LibraryCatalogEntry] = []
}
"""
        originals = {"LibraryCatalog.swift": source}
        exported = importer.export_catalogue(originals)
        entry = importer.load_json(exported, "export.json")[0]
        self.assertEqual(entry["officialLinks"][0]["title"], "Original")
        self.assertEqual(entry["template"]["typicalDoseValue"], 2.5)
        self.assertEqual(entry["template"]["halfLife"]["lowerHours"], 4)
        self.assertEqual(entry["template"]["blend"], ["catalog:peptide:other"])
        self.assertEqual(
            entry["template"]["typicalRecurrence"]["weekdays"]["_0"], [1, 3, 5]
        )
        self.assertEqual(originals["LibraryCatalog.swift"], source)
        self.assertEqual(exported, importer.export_catalogue(originals))

    def test_changed_accessor_cannot_silently_export_another_catalogue(self):
        with self.assertRaisesRegex(importer.ImportFailure, "authoredEntries"):
            importer.export_catalogue({"LibraryCatalog.swift": b"enum LibraryCatalog {}"})


if __name__ == "__main__":
    unittest.main()
