import contextlib
import hashlib
import io
import json
from pathlib import Path
import runpy
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LegacyBaselineTests(unittest.TestCase):
    def test_authored_records_are_unchanged(self):
        baseline = json.loads((ROOT / "tests/fixtures/legacy-baseline.json").read_text())
        for name, expected in baseline["datasets"].items():
            with self.subTest(dataset=name):
                raw = (ROOT / name).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), expected["sha256"])
                self.assertEqual(sorted(json.loads(raw)), expected["slugs"])

    def test_build_preserves_routes_exports_and_favorite_keys(self):
        baseline = json.loads((ROOT / "tests/fixtures/legacy-baseline.json").read_text())
        namespace = runpy.run_path(str(ROOT / "generate.py"), run_name="legacy_test")
        with tempfile.TemporaryDirectory() as directory:
            namespace["main"].__globals__["OUT"] = directory
            with contextlib.redirect_stdout(io.StringIO()):
                namespace["main"]()
            output = Path(directory)
            routes = sorted(str(p.relative_to(output)) for p in output.rglob("*.html"))
            expected_routes = list(baseline["core_routes"])
            for name, prefix in (
                ("peptides.json", "peptides"),
                ("stacks.json", "stacks"),
                ("categories.json", "categories"),
            ):
                expected_routes += [
                    f"{prefix}/{slug}.html"
                    for slug in baseline["datasets"][name]["slugs"]
                ]
                self.assertEqual(
                    json.loads((output / "data" / name).read_text()),
                    json.loads((ROOT / name).read_text()),
                )
            self.assertLessEqual(set(expected_routes), set(routes))
            for name, prefix in (("peptides.json", "peptide"), ("stacks.json", "stack")):
                for slug in baseline["datasets"][name]["slugs"]:
                    page = output / f"{prefix}s/{slug}.html"
                    self.assertIn(f'data-fav-key="{prefix}:{slug}"', page.read_text())
            self.assertIn("'pw_favorites'", (output / "assets/site.js").read_text())
            self.assertLessEqual(set(baseline["output_roots"]), {p.name for p in output.iterdir()})
            self.assertFalse((output / "research").exists())
            self.assertNotIn("catalog:context:sleep", (output / "llms.txt").read_text())

    def test_all_legacy_relationships_resolve(self):
        peptides = json.loads((ROOT / "peptides.json").read_text())
        categories = json.loads((ROOT / "categories.json").read_text())
        stacks = json.loads((ROOT / "stacks.json").read_text())
        for slug, entry in peptides.items():
            with self.subTest(slug=slug):
                self.assertTrue(entry["categories"])
                self.assertLessEqual(set(entry["categories"]), categories.keys())
                self.assertLessEqual(set(entry["related"]), peptides.keys())
                for related in entry.get("mixing_notes", {}).values():
                    self.assertLessEqual(set(related), peptides.keys())
        for slug, entry in stacks.items():
            with self.subTest(stack=slug):
                self.assertLessEqual(set(entry["component_slugs"]), peptides.keys())


if __name__ == "__main__":
    unittest.main()
