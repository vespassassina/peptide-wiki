import contextlib
from copy import deepcopy
import hashlib
from html import escape
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urljoin, urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.json_scripts = []
        self.in_json = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for name in ("href", "src", "action"):
            if name in attrs:
                self.urls.append(attrs[name])
        self.in_json = tag == "script" and attrs.get("type") in {
            "application/ld+json", "application/json"
        }

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_json = False

    def handle_data(self, data):
        if self.in_json:
            self.json_scripts.append(json.loads(data))


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace = runpy.run_path(str(ROOT / "generate.py"), run_name="site_test")
        cls.directory = tempfile.TemporaryDirectory()
        cls.output = Path(cls.directory.name)
        cls.namespace["main"].__globals__["OUT"] = str(cls.output)
        with contextlib.redirect_stdout(io.StringIO()):
            cls.namespace["main"]()

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_broad_pages_and_machine_exports_are_complete(self):
        public = json.loads((self.output / "data/library.json").read_text())
        self.assertEqual(len(public["entries"]), 245)
        for entry in public["entries"].values():
            self.assertTrue((self.output / entry["path"].lstrip("/")).is_file())
            parser = Links()
            parser.feed((self.output / entry["path"].lstrip("/")).read_text())
            linked_paths = {urlsplit(urljoin("https://example.org" + entry["path"], url)).path for url in parser.urls}
            for related in entry["related"]:
                self.assertIn(public["entries"][related]["path"], linked_paths)
        for kind in self.namespace["KIND_LABELS"]:
            self.assertTrue((self.output / f"kinds/{kind}.html").is_file())
        self.assertIn("Caffeine", (self.output / "directory.html").read_text())
        self.assertIn("Biohacker Wiki", (self.output / "index.html").read_text())
        self.assertIn("Caffeine", (self.output / "llms.txt").read_text())
        urls = ET.parse(self.output / "sitemap.xml").findall(".//{*}loc")
        self.assertEqual(len(urls), len(list(self.output.rglob("*.html"))))
        self.assertEqual(len(urls), 277)
        self.assertTrue(all(item.text.startswith("https://vespassassina.github.io/peptide-wiki/") for item in urls))

    def test_attribution_and_historical_states_are_rendered(self):
        bpc = (self.output / "peptides/bpc-157.html").read_text()
        self.assertIn("Half-life estimates differ", bpc)
        self.assertIn("Sprague-Dawley", bpc)
        self.assertIn("4–6", bpc)
        empty = (self.output / "library/medication-paracetamol.html").read_text()
        self.assertIn("2026-10-06", empty)
        self.assertIn("No suitable community description", empty)
        self.assertIn("not establish", empty)
        stack = (self.output / "stacks/bpc-157-tb-500.html").read_text()
        self.assertIn("statements conflict", stack)
        tb_legacy = (self.output / "peptides/tb-500.html").read_text()
        tb_fragment = (self.output / "library/peptide-tb-500.html").read_text()
        self.assertIn('href="../library/peptide-tb-500.html"', tb_legacy)
        self.assertIn('href="../peptides/tb-500.html"', tb_fragment)

    def test_category_cards_and_pages_cover_all_kinds_with_matching_counts(self):
        public = json.loads((self.output / "data/library.json").read_text())
        home = (self.output / "index.html").read_text()
        self.assertIn("Browse by category", home)
        self.assertNotIn("Legacy library by benefit", home)
        for slug, category in public["categories"].items():
            members = [public["entries"][key] for key in category["members"]]
            card = home.split(f'data-category="{slug}"', 1)[1].split("</a>", 1)[0]
            self.assertIn(f'{len(members)} entries', card)
            document = (self.output / f"categories/{slug}.html").read_text()
            parser = Links()
            parser.feed(document)
            structured = next(value for value in parser.json_scripts if value.get("@type") == "CollectionPage")
            self.assertEqual({part["url"] for part in structured["hasPart"]}, {entry["path"] for entry in members})
            for kind, label in self.namespace["KIND_LABELS"].items():
                count = sum(entry["kind"] == kind for entry in members)
                if count:
                    self.assertIn(f'<div data-kind="{kind}"><dt>{escape(label)}</dt><dd>{count}</dd></div>', card)
                    self.assertIn(f'id="type-{kind}"', document)
                else:
                    self.assertNotIn(f'data-kind="{kind}"', card)
            self.assertIn("not evidence of benefit", document)

    def test_category_navigation_and_machine_data_keep_legacy_compatibility(self):
        public = json.loads((self.output / "data/library.json").read_text())
        sitemap = json.loads((self.output / "data/sitemap.json").read_text())
        for name in ("peptides", "categories", "stacks"):
            self.assertEqual(json.loads((self.output / f"data/{name}.json").read_text()),
                             json.loads((ROOT / f"{name}.json").read_text()))
        for slug, category in public["categories"].items():
            self.assertEqual(sitemap["categoryEntries"][slug], category["members"])
            self.assertEqual(sitemap["categories"][slug], self.namespace["CAT_PEPTIDES"][slug])
        for entry in public["entries"].values():
            if entry["id"].startswith("library:"):
                document = (self.output / entry["path"].lstrip("/")).read_text()
                for slug in entry["categories"]:
                    self.assertIn(f'href="../categories/{slug}.html"', document)

    def test_public_wiki_uses_neutral_research_labels_without_source_branding(self):
        branded = [
            path.relative_to(self.output).as_posix()
            for path in self.output.rglob("*")
            if path.is_file() and b"biometra" in path.read_bytes().lower()
        ]
        self.assertEqual(len(branded), 0, f"Public output still contains source branding: {branded[:8]}")
        bpc = (self.output / "peptides/bpc-157.html").read_text()
        self.assertEqual(bpc.count('id="research"'), 1)
        self.assertEqual(bpc.count('id="research-records"'), 1)
        self.assertIn('href="#research-records">Research records</a>', bpc)
        self.assertIn('href="#research">Research summary</a>', bpc)
        self.assertIn("Historical checks dated 2026-10-06 retain their original scope", bpc)

    def test_no_archive_defaults_or_false_review_dates_in_public_output(self):
        forbidden = {"template", "typicalDoseValue", "typicalRecurrence", "vialContentsValue", "usageNote"}

        def check_keys(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden.intersection(value))
                for item in value.values():
                    check_keys(item)
            elif isinstance(value, list):
                for item in value:
                    check_keys(item)

        check_keys(json.loads((self.output / "data/library.json").read_text()))
        for path in self.output.rglob("*"):
            self.assertNotIn("audit", path.parts)
            self.assertNotIn("research", path.parts)
            if path.suffix == ".html":
                text = path.read_text()
                self.assertNotIn('"lastReviewed"', text)
                self.assertNotIn("Reviewed " + self.namespace["TODAY"], text)
                self.assertNotIn('"typicalDoseValue"', text)
        # A rejected proposal is retained only in the archive, not in accepted outputs.
        rejected = json.loads((ROOT / "research/biometra/audit/B-82/candidate-research.json").read_text())
        candidate = rejected["entries"].get("catalog:food-protocol:extended-fast", {})
        for item in candidate.get("community", []):
            if item.get("description"):
                self.assertNotIn(item["description"], (self.output / "library/food-protocol-extended-fast.html").read_text())

    def test_publication_limits_are_visible_and_unverified_accounts_are_not_quotations(self):
        dhea = (self.output / "library/hormone-dhea.html").read_text()
        self.assertIn("Publication suitability", dhea)
        self.assertIn("100 mg", dhea)
        self.assertIn("Source-support limitation", dhea)
        self.assertIn('<details class="research-account">', dhea)
        self.assertNotIn('<blockquote class="research-account">', dhea)
        self.assertIn("Unverified imported account", dhea)
        account = dhea.split('<details class="research-account">', 1)[1]
        self.assertLess(account.index("100 mg was not verified"), account.index("Imported wording:"))
        self.assertNotIn("What the source supports", dhea)
        sleep = (self.output / "library/context-sleep.html").read_text()
        self.assertIn("not a clinical verification", sleep)
        self.assertIn("not independently verified", (self.output / "about.html").read_text())

    def test_every_local_link_resolves_under_root_and_pages_subpath(self):
        for path in self.output.rglob("*.html"):
            parser = Links()
            parser.feed(path.read_text())
            relative = path.relative_to(self.output).as_posix()
            for prefix in ("/", "/peptide-wiki/"):
                base = "https://example.org" + prefix + relative
                for href in parser.urls:
                    url = urlsplit(urljoin(base, href))
                    if url.hostname != "example.org":
                        continue
                    self.assertTrue(url.path.startswith(prefix), (relative, href))
                    target = url.path[len(prefix):]
                    self.assertTrue((self.output / target).exists(), (relative, href, target))

    def test_hostile_text_cannot_escape_embedded_json_or_html(self):
        namespace = self.namespace["page"].__globals__
        title = '</script><script>alert("injected")</script>'
        page = namespace["page"](title, title, "", namespace["esc"](title))
        self.assertNotIn(title, page)
        self.assertIn("\\u003c/script", page)
        parser = Links()
        parser.feed(page)
        entry = deepcopy(namespace["LIBRARY"]["entries"]["library:hormone-dhea"])
        entry["research"][0]["publicationReview"]["notices"] = [title]
        research = namespace["research_block"](entry)
        self.assertNotIn(title, research)
        self.assertIn("&lt;/script&gt;", research)

    def test_failed_input_and_render_leave_previous_output_untouched(self):
        namespace = self.namespace["main"].__globals__
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "research", root / "research")
            for name in ("peptides.json", "categories.json", "stacks.json"):
                shutil.copyfile(ROOT / name, root / name)
            output = root / "out"
            output.mkdir()
            marker = output / "previous.html"
            marker.write_text("last successful build")
            (root / "research/biometra/evidence.json").write_text("{}")
            with patch.dict(namespace, SRC=str(root), OUT=str(output)):
                with self.assertRaises(ValueError):
                    namespace["main"]()
            self.assertEqual(list(output.iterdir()), [marker])
            self.assertEqual(marker.read_text(), "last successful build")
            with patch.dict(namespace, OUT=str(output)):
                with patch.object(namespace["shutil"], "copyfile", side_effect=OSError("Disk full")):
                    with self.assertRaises(OSError):
                        namespace["main"]()
            self.assertEqual(marker.read_text(), "last successful build")
            self.assertEqual(list(root.glob(".wiki-build-*")), [])

    def test_symlink_output_is_not_followed(self):
        namespace = self.namespace["main"].__globals__
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "other"
            target.mkdir()
            link = root / "out"
            link.symlink_to(target, target_is_directory=True)
            with patch.dict(namespace, OUT=str(link)), self.assertRaises(ValueError):
                namespace["main"]()
            self.assertTrue(link.is_symlink())
            self.assertEqual(list(target.iterdir()), [])

    def test_archive_sentinels_cannot_enter_any_public_projection(self):
        namespace = self.namespace["main"].__globals__
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "research", root / "research")
            for name in ("peptides.json", "categories.json", "stacks.json"):
                shutil.copyfile(ROOT / name, root / name)
            bundle = root / "research/biometra"
            authored_path = bundle / "audit/catalogue-authored.json"
            authored = json.loads(authored_path.read_text())
            authored[0]["template"]["usageNote"] = "ARCHIVED_APP_DEFAULT_SENTINEL"
            authored_path.write_text(json.dumps(authored))
            audit_path = bundle / "audit/B-82/candidate-research.json"
            audit = json.loads(audit_path.read_text())
            audit["entries"]["catalog:food-protocol:extended-fast"]["community"][0]["description"] = "REJECTED_DRAFT_SENTINEL"
            audit_path.write_text(json.dumps(audit))
            manifest_path = bundle / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            for record in manifest["files"] + [manifest["authoredExport"]]:
                record["sha256"] = hashlib.sha256((bundle / record["targetPath"]).read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest))
            with patch.dict(namespace, SRC=str(root), OUT=str(root / "out")):
                with contextlib.redirect_stdout(io.StringIO()):
                    namespace["main"]()
            for output in (root / "out").rglob("*"):
                if output.is_file():
                    raw = output.read_bytes()
                    self.assertNotIn(b"ARCHIVED_APP_DEFAULT_SENTINEL", raw)
                    self.assertNotIn(b"REJECTED_DRAFT_SENTINEL", raw)


if __name__ == "__main__":
    unittest.main()
