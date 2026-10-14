# Biohacker Wiki consolidation plan

Scope: [approved specification](specs/biohacker-wiki-consolidation.md).
Sprint 1 was reviewed, then the user explicitly authorised autonomous completion
of all remaining approved work. All five sprints are complete locally. No
publication or remote operation is authorised.

## Epic A: Reproducible, lossless import

Sprint 1 delivers a pinned, auditable research bundle while the existing wiki
continues to build unchanged.

| Task | Outcome and proof | Status |
| --- | --- | --- |
| preserve-baseline | Exact 79/8/8 authored data hashes, 103 routes, exports and favorite keys protected by tests | Done |
| export-authored-catalogue | All 210 authored entries exported from scratch copies; complete Codable equality, original links and deterministic weekday sets | Done |
| import-pinned-research | Canonical evidence/ledger and labelled audit pack preserved; counts/hashes, no-op reimport and invalid-input guards verified | Done |

## Epic B: Identity and evidence reconciliation

Sprint 2 delivers the unified catalogue projection without guessing ambiguous
identities or overwriting legacy text.

| Task | Outcome and proof | Status |
| --- | --- | --- |
| map-catalogue-identities | All 210 source IDs mapped: 44 legacy attachments, 166 new identities, 245 canonical entries | Done |
| reconcile-evidence | Every canonical field/claim origin and final ledger outcome reconciled; explicit conflicts and circular sources | Done |

## Epic C: Readable research

Sprint 3 delivers complete local research pages for legacy and new entities.

| Task | Outcome and proof | Status |
| --- | --- | --- |
| render-research-pages | Summary/verdict, all five study fields, separate community/negative findings, uncertainty and historical dates rendered | Done |
| enforce-public-boundary | Mutated audit/default sentinels absent from every public file; historical PK context separate, no calculator autofill | Done |

## Epic D: Consistent identity and discovery

Sprint 4 delivers locally usable Biohacker Wiki branding and catalogue discovery.

| Task | Outcome and proof | Status |
| --- | --- | --- |
| extend-discovery | All eight kinds reachable; research/name/alias search, kind filter, keyboard sorting and empty feedback | Done |
| preserve-favorites | Old cookie/keys plus new favorites work at root and Pages base; explicit malformed/unwritable-cookie errors | Done |
| brand-site-exports | Biohacker Wiki branding; full catalogue JSON, 277-page absolute sitemap and broad llms.txt; original exports retained | Done |

## Epic E: Verified handoff

Sprint 5 delivers the tested local consolidation, not a public release.

| Task | Outcome and proof | Status |
| --- | --- | --- |
| verify-consolidation | 32 tests and real build; exact preservation, full field/origin reconciliation, idempotency and failure isolation | Done |
| verify-browser-flows | 12 viewport/theme/base-path flows; 14 final screenshots, keyboard, cookie failures and unchanged calculator | Done |
| document-handoff | README/contributing/spec/decisions updated; verification and publication limits recorded below | Done |

## Prerequisites and working rules

Baseline preservation and authored export are independent. Import requires both.
Identity mapping requires import; reconciliation requires mapping; rendering
requires reconciliation; public-boundary verification requires rendering.
Discovery and favorites require rendered pages and the public boundary.
Branding/exports require those routes. Final end-to-end and browser checks require
the finished site; final documentation requires their evidence.

Behavioural tests preceded each implementation workstream. The user-directed
continuation replaced the original sprint-stop boundary. Record future decisions
in DECISIONS.md and unfinished work in HANDOFF.md. Keep SQL tracking aligned.

No push, PR, CI change, repository rename or publication is authorised.
Fresh live source/rights suitability checks remain a separate future release
gate. Historical research dates must not become build-time review dates.

## Actual verification: 2026-10-14

| Check | Observed result |
| --- | --- |
| `python3 -B -m unittest discover -s tests` | 32 passed, no skips; Swift exporter/round-trip tests included |
| `python3 -B generate.py` | 245 reference entries, 8 stacks, 8 legacy categories; 277 HTML pages |
| `env PATH=/nonexistent /usr/bin/python3 -B generate.py` | Same successful build without a compiler or other executable on PATH |
| Actual pinned importer with `--write` | `Already identical`; all 210/543/270/163/210 counts and 130 final outcomes reconcile |
| Source `git status --short` / HEAD | Clean; still `adc7684614f9439b41d91a3312b62e7982c7e20e` |
| Legacy preservation | Exact original JSON hashes and content; every old URL/export/favorite key retained |
| Complete public projection | Every canonical evidence field, study/community origin, original link and final ledger record compared with pinned input |
| Local-link/JSON/XML checks | All HTML links resolve at `/` and `/peptide-wiki/`; all embedded JSON parses; sitemap covers exactly 277 pages |
| Failure isolation | Corrupt evidence and simulated disk-write failure leave prior output intact; output symlinks rejected |
| Archive boundary | Default-note and rejected-draft sentinels injected into a temporary valid bundle remain absent from every public file |
| Hostile inputs | Duplicate IDs/keys, bad pins/counts/URLs/paths/ledger shapes, script-closing text and malformed cookies handled without silent success |
| JavaScript syntax | `node --check` passed for generated site JS and the optional browser checker |
| Browser matrix | Chromium 156.0.8078.4; 375/768/1440 CSS pixels × light/dark × root/Pages base: all 12 flows passed, no uncaught page errors |
| Browser interactions | Search form/query, kind filter, keyboard sort/menu, no-results, old/new favorite persistence/removal, historical/empty findings, file-open links and calculator invalid input passed |
| Cookie failure boundary | Malformed cookie visible; simulated browser cookie-write rejection gives an actionable error and does not show a saved state |
| Visual review | Mobile/tablet/desktop, both themes, menu/focus, directory/empty, favorites/errors, research/long URLs and unchanged calculator captured; mobile sidebar/table readability repaired |
| Design detector | Bounded static pass found no deterministic issues; post-edit CSS hooks also clean |
| Repository checks | `git diff --check` clean; legacy JSON, source bundle, CI and remote URL unchanged |

Fourteen final PNGs and `results.json` are session artifacts under
`files/browser-check/screenshots/` in session
`023e5684-81e6-4e42-ae5d-d8b4f27f282b`. Home screenshots cover all six
viewport/theme combinations. Additional captures are `mobile-menu.png`,
`directory-filter.png`, `directory-empty.png`, `favorites.png`,
`malformed-favorites.png`, `bpc-research.png`, `bounded-empty-finding.png` and
`calculator-unchanged.png`. The reproducible checker is
`scripts/check_browser.cjs`; installation/run commands are in the README.
Screenshots are not copied into deploy output.

Hand-traced BPC-157 retains the in-vitro approximately 40-minute legacy account
and the source's 4-6-hour preclinical note as differing measurements. Its rat
study retains population, regimen, duration, outcome and source. Sleep retains
its attributed practice account. Paracetamol retains the dated, bounded empty
finding. The rejected extended-fast candidate remains audit-only.

Skipped deliberately: fresh live clinical/source-suitability/rights review,
public-site verification, push, PR, deployment, remote repository rename and
native-device/other-browser testing. Browser checks used local Chromium;
historical claims are not certified current. The local app's project-display
label is not changed through an unsupported API. These limits do not block the
approved local consolidation, but this is not a release approval.
