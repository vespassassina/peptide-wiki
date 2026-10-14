# Biohacker Wiki consolidation plan

Scope: [approved specification](specs/biohacker-wiki-consolidation.md).
Only Sprint 1 is approved. Stop for review before continuing.

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
| map-catalogue-identities | Explicit disposition for every source ID; old routes retained; variants/esters/blends kept distinct | Pending approval |
| reconcile-evidence | Attributed attachments, exact deduplication and visible conflicts; no circular-source inflation | Pending approval |

## Epic C: Readable research

Sprint 3 delivers complete local research pages for legacy and new entities.

| Task | Outcome and proof | Status |
| --- | --- | --- |
| render-research-pages | Summary/verdict, all five study fields, separate community/negative findings, uncertainty and historical dates rendered | Pending approval |
| enforce-public-boundary | Sentinel audit/default text absent from every public projection; approved PK context visible, no calculator autofill | Pending approval |

## Epic D: Consistent identity and discovery

Sprint 4 delivers locally usable Biohacker Wiki branding and catalogue discovery.

| Task | Outcome and proof | Status |
| --- | --- | --- |
| extend-discovery | Every kind reachable through home/directory/search while benefit browsing remains intact | Pending approval |
| preserve-favorites | Old cookie/keys and new favorites persist across views and correct Pages-base links | Pending approval |
| brand-site-exports | Consistent branding and broad machine outputs; old routes/endpoints and repository/public URL unchanged | Pending approval |

## Epic E: Verified handoff

Sprint 5 delivers the tested local consolidation, not a public release.

| Task | Outcome and proof | Status |
| --- | --- | --- |
| verify-consolidation | Full preservation/count/offline/idempotency/failure-isolation/adversarial checks and actual Python build | Pending approval |
| verify-browser-flows | Screenshots and interactions at 375/768/1440 widths, light/dark, keyboard, root/subpath, no calculator autofill | Pending approval |
| document-handoff | Reproducible commands, actual evidence/skipped checks, maintenance rules and fresh suitability/rights release gate | Pending approval |

## Prerequisites and working rules

Baseline preservation and authored export are independent. Import requires both.
Identity mapping requires import; reconciliation requires mapping; rendering
requires reconciliation; public-boundary verification requires rendering.
Discovery and favorites require rendered pages and the public boundary.
Branding/exports require those routes. Final end-to-end and browser checks require
the finished site; final documentation requires their evidence.

Each task starts with a failing behavioural test. Each sprint stops with a
working increment for review/re-planning. Record decisions in DECISIONS.md and
unfinished work in HANDOFF.md. Keep SQL task tracking aligned with this plan.

No push, PR, CI change, repository rename or publication is authorised.
Fresh live source/rights suitability checks remain a separate future release
gate. Historical research dates must not become build-time review dates.
