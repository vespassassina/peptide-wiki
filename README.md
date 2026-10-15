# Biohacker Wiki

**Unchanged public URL: https://vespassassina.github.io/peptide-wiki/**

A source-attributed static reference for peptides, medications and hormones,
supplements, food and fasting, exercise, recovery practices, habits and lab
markers. The library has **245 reference entries**: all 79 legacy
records plus all 210 Biometra records, with 44 explicit identity overlaps.
The original 8 benefit categories and 8 stacks remain available.

This is not medical advice. Study reports, community descriptions, regulatory
statements and uncertainty stay separate. Imported research is a historical
snapshot, not fresh clinical verification. Conflicting accounts are retained,
not averaged. The site/project name changes; `vespassassina/peptide-wiki` does not.

Published at the unchanged URL above. The 2026-10-15 suitability/rights review
covers an explicitly historical reference, not clinical certification. Unverified
community accounts are collapsed and labelled; identified source-support gaps
remain visible. Publication uses the existing GitHub Pages workflow and URL.

## What's here

- `peptides.json`, `categories.json`, `stacks.json` — unchanged legacy authored content.
- `research/biometra/` — pinned evidence, final outcome ledger and non-deployed audit archive.
- `research/mapping.json` — explicit identity dispositions, variant distinctions and conflicts.
- `library.py` — validated, allowlisted public projection with citation occurrence provenance.
- `generate.py` — offline, atomic static-site build.
- `vendor/artifactkit/` — the CSS/JS design system the site is built on.
- `out/` — build output (gitignored, generated locally).

## Building the site

Needs Python 3.9 or later, with no third-party packages, Swift or source checkout.

```sh
python3 -B generate.py
```

The 277 HTML pages and machine exports land in `out/`. Inputs are validated and
the entire build succeeds before the old output is replaced. Invalid inputs or a
render/write failure retain the previous successful output.

Open `out/index.html` directly, or serve it locally:

```sh
python3 -m http.server --bind 127.0.0.1 --directory out
```

Favorites need an HTTP origin; browser cookie restrictions make `file://`
persistence unreliable. Old `pw_favorites` keys remain compatible. New entries
use a distinct `library:` namespace. Generated links also work under the
unchanged `/peptide-wiki/` Pages base.

`data/library.json` contains the full public catalogue and attributed research.
The original `data/peptides.json`, `data/categories.json` and `data/stacks.json`
remain compatible. The sitemap and `llms.txt` enumerate the broader library.

## Biohacker Wiki consolidation

The pinned import preserves all 210 authored records, 543 top-level source-link
occurrences, 270 study protocols, 163 community descriptions, 210 verdicts and
130 final B-82 outcomes (59 verified descriptions; 71 bounded empty findings).
These are source occurrences, not independent studies. Thirty source links
point back to this wiki and are labelled circular provenance.

See the [specification](docs/specs/biohacker-wiki-consolidation.md),
[completed sprint plan and verification evidence](docs/PLAN.md) and
[decisions](docs/DECISIONS.md).

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

The manifest records source paths/hashes, authority, counts, transformations,
status labels and exclusions. No bundle file is copied wholesale into `out/`.
The public projection selects accepted research fields only. Complete app
templates/default doses/schedules, blends and checked-in intermediate/rejected
B-82 drafts stay in the non-rendered, non-deployed audit archive. They are not
searchable assertions, recommendations or calculator presets. Sourced PK context
is displayed separately with uncertainty and conflicting estimates.

Publisher caches/excerpts, local-only archives, private health/store data and
credentials are excluded. Historical retrieval paths in the audit inventory are
references, not included publisher material.

Source checks are historical, not fresh clinical verification. New public
republication requires separate suitability/rights checks and user permission.
The current review is in `research/publication-review.json`; source availability
for all 888 citation URLs is recorded separately in
`research/citations-live-checks.json`. Availability failures remain visible on
affected source references. Neither HTTP success nor the review date certifies a
medical claim. The reports themselves are excluded from generated output.

## Checks

```sh
python3 -B -m unittest discover -s tests
python3 -B generate.py
```

The exporter tests use Swift when available and explicitly skip if it is absent.
All preservation, bundle-integrity and Python import-validation checks still run;
ordinary site generation does not need Swift or the Biometra checkout.

For the optional browser checks, install the verification-only tool in scratch,
not the repository. It is not a production/build dependency:

```sh
npm install --prefix /path/to/scratch playwright@1.64.1
PLAYWRIGHT_BROWSERS_PATH=/path/to/scratch/browsers /path/to/scratch/node_modules/.bin/playwright install chromium
NODE_PATH=/path/to/scratch/node_modules PLAYWRIGHT_BROWSERS_PATH=/path/to/scratch/browsers \
  node scripts/check_browser.cjs /path/to/screenshots
```

The script starts and closes its own loopback server. It checks root and Pages
subpaths at 375/768/1440 CSS pixels in light/dark modes, keyboard navigation,
search/sorting, old/new favorites, cookie errors, historical/empty research and
unchanged calculator behaviour.
It also checks navigation at 320/375/714/768/860/861/1024/1440 CSS pixels in
both themes, including Escape/focus return, outside clicks, tabbing out,
breakpoint resets and short-screen scrolling. Two no-JavaScript cases ensure
the links remain available without a working disclosure script. Four additional
menu screenshots and four publication-warning/account screenshots bring the
total to 22, alongside `results.json`.
External browser requests are blocked. Run the Python build first.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Edit authored data or reviewed mappings,
not generated HTML. Keep the pinned bundle immutable; a future source update
needs a new reviewed pin and migration, never a silent overwrite.

## Structure of an entry

Each peptide in `peptides.json` has: name, aliases, categories, status (research-only, prescription, etc.), origin, mechanism, reported benefits, dosing protocols as reported by the community, side effects, safety notes, citations, and related peptides. Look at an existing entry before adding a new one — consistency matters more than creativity here.

## License

MIT. See [LICENSE](LICENSE). This does not establish republication rights for
linked third-party material. Content is provided as-is; verify anything before
acting on it.
