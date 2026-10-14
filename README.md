# Peptide Wiki

**Live site: https://vespassassina.github.io/peptide-wiki/**

A static reference site for research peptides: mechanism, dosing protocols reported in the community, safety notes, and citations. 79 peptides across 8 categories, plus 8 common stacks.

This is not medical advice. Most of these compounds are unregulated, sold for research use only, and have thin or no human trial data. The site says so on every page. Read it as a research summary, not a green light.

## What's here

- `peptides.json`, `categories.json`, `stacks.json` — the actual content.
- `generate.py` — builds the static HTML site from those three files.
- `vendor/artifactkit/` — the CSS/JS design system the site is built on.
- `out/` — build output (gitignored, generated locally).
- `research/biometra/` — pinned research and audit archive for the planned Biohacker Wiki consolidation; not rendered or copied into `out/`.

## Building the site

Needs Python 3, no dependencies.

```
python3 generate.py
```

Output lands in `out/`. Open `out/index.html` directly in a browser, or serve the folder (`python3 -m http.server -d out`) — some features, like the favorites list, need a real HTTP origin to work properly (browsers isolate cookies per `file://` page).

## Biohacker Wiki consolidation

Sprint 1 preserves all 210 Biometra catalogue records, 543 source-link occurrences,
270 study protocols, 163 community descriptions, and the final 130-entry B-82
outcome ledger. Checked-in rejected/intermediate drafts and app defaults are
archived, not accepted article content, recommendations or calculator presets.
The site is not yet rebranded or extended to show these records.

See the [specification](docs/specs/biohacker-wiki-consolidation.md),
[sprint plan](docs/PLAN.md) and [handoff](docs/HANDOFF.md).
The eventual name is Biohacker Wiki; the repository and public URL stay unchanged.

To preview the reproducible import, use the approved isolated Biometra worktree
at commit `adc7684614f9439b41d91a3312b62e7982c7e20e`:

```sh
python3 scripts/import_biometra.py --source /absolute/path/to/approved/biometra-worktree
```

Migration alone requires a Swift 6 compiler. It compiles temporary copies of the
domain files, preserves original authored links/templates, and verifies complete
Codable round trips. No source files are changed and no dependencies are fetched.
Add `--write` to persist a fully validated import. An identical bundle is a no-op;
a differing existing bundle is rejected, not overwritten.

The manifest records source paths/hashes, authority, counts, export
transformations and exclusions. All files in the bundle remain outside deploy
output. Do not copy its directory into `out/`; future public projections require
an explicit field allowlist. Publisher caches/excerpts, local-only archives,
private health data and credentials are excluded.

Source checks are historical, not fresh clinical verification. New public
republication requires separate suitability/rights checks and user permission.

## Checks

```sh
python3 -B -m unittest discover -s tests
python3 generate.py
```

The exporter tests use Swift when available and explicitly skip if it is absent.
All preservation, bundle-integrity and Python import-validation checks still run;
ordinary site generation does not need Swift or the Biometra checkout.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: fix a dosing number, add a missing citation, correct a mechanism description, or add a peptide that's missing. Open a PR against the JSON files, not the generated HTML.

## Structure of an entry

Each peptide in `peptides.json` has: name, aliases, categories, status (research-only, prescription, etc.), origin, mechanism, reported benefits, dosing protocols as reported by the community, side effects, safety notes, citations, and related peptides. Look at an existing entry before adding a new one — consistency matters more than creativity here.

## License

MIT. See [LICENSE](LICENSE). Content is provided as-is — verify anything before acting on it.
