# Biohacker Wiki consolidation

Approved scope: all 210 Biometra catalogue records. After Sprint 1 review, the
user explicitly authorised autonomous completion of the remaining scope.
The original sprint-stop boundary is superseded; the publication boundary is not.

## Goal and boundaries

Consolidate Biometra's checked-in authored research into this existing static
reference. Rename the site/project-facing identity to **Biohacker Wiki**, while
keeping `vespassassina/peptide-wiki` and
`https://vespassassina.github.io/peptide-wiki/` unchanged.

Preserve all existing wiki content, citations, routes, exports and favorites.
Distinguish evidence from anecdote and uncertainty. Deduplicate without silently
losing differing assertions, variants, negative findings or provenance.

The user explicitly selected preservation of checked-in intermediate/rejected
B-82 drafts in a non-rendered audit archive. The user also confirmed that all
app templates/default doses/schedules stay in non-rendered, non-deployed
provenance. Show sourced research protocols and pharmacokinetic context
separately; never use app defaults as recommendations or calculator autofill.

Do not modify the source checkout, rename the remote repository, change CI,
push, open a PR, deploy or publish. Exclude private health/store data,
credentials, ignored/untracked files, local-only archives, publisher HTML/text
caches and publisher excerpts. No new framework, personal treatment advice,
scheduling or automatic synchronisation.

## Verified starting point

Target baseline commit: `5b66ac030272f1802aae4c0812eef6c3fdacb082`.
The wiki has 79 peptide records, 8 stacks and 8 benefit categories, with 183
citation occurrences and 175 distinct citation URLs. All recorded relationships
resolve. The dependency-free Python build generates 103 HTML pages.
The pre-migration README incorrectly reported 72 entries.

No importer, tests, schema validator or project-specific agent instructions were
present. The current generator is tightly peptide-specific. Artifactkit is the
existing visual authority; retain its styling and reading layout.

Source commit: `adc7684614f9439b41d91a3312b62e7982c7e20e` in
`vespassassina/BiohackerAssistant` (public application name: Biometra).
Only the explicitly approved isolated worktree may be read for migration.

| Source | Authority |
| --- | --- |
| `scripts/evidence/evidence.json` | Canonical evidence: 210 records, 543 top-level source links, 270 study protocols, 163 community descriptions, 210 verdicts |
| `HealthAgentKit/Sources/HealthAgentDomain/LibraryCatalog.swift` | 210 authored IDs, names, kinds, summaries, uncertainty, original links, templates and PK context |
| `scripts/evidence/community-research.json` | Final 130-entry B-82 ledger: 59 verified-description and 71 no-verified-description outcomes |
| `docs/research/B-82/catalogue-evidence.json` | Dated 130-entry snapshot; not the current evidence source |
| `docs/research/B-82/research-outcomes.json` | Dated final ledger; byte-identical to the canonical ledger at this pin |
| Other tracked B-82 material | Audit proposals/reviews/overrides/retrieval metadata; not automatically approved assertions |
| `LibraryCatalogEvidence.swift` | Generated compilation dependency; not independent research |

Source ID namespaces cover hormone (44), medication (26), supplement (49),
food-protocol (16), exercise (16), recovery (17), peptide (36), context (5) and
lab-marker (1). Preserve both namespace and actual `ItemKind`; they differ.
Counts describe occurrences, not independent studies. Thirty top-level links
point back to this wiki and are circular provenance.

## Storage and reproducibility

Keep `peptides.json`, `stacks.json` and `categories.json` as canonical legacy
authored data. Add a pinned bundle under `research/biometra/`:

- Unmodified canonical evidence and final community ledger.
- A manifest with original paths/hashes, authority, counts and exclusions.
- `audit/catalogue-authored.json`, a complete Codable export including templates.
- The original authored Swift source and the selected tracked B-82 audit pack.
- An explicit identity/conflict mapping in Sprint 2.

Use a target-owned Python importer and minimal Swift exporter. Compile only
scratch copies of Foundation-only domain sources; expose only the copied
`authoredEntries` accessor. Do not export `builtInEntries`, whose runtime overlay
overwrites authored links. Preserve the original source bytes/hash and record
the access-only transformation. Sort the weekday Set's encoded array for
determinism, then decode and compare complete entries to prove value equality.
Do not sort other arrays or change study/regimen order.

Validate the complete input before persisting. Reject duplicate keys/IDs, source
pin/hash drift, invalid references, unsafe URLs/paths and irreconcilable counts.
Preserve unexpected metadata or reject it explicitly, never silently discard it.
An identical reimport must be a no-op. Never silently overwrite a differing
existing bundle. Normal site builds use checked-in target data only: no Swift,
source checkout, network or third-party Python packages.

All archive content is excluded from deploy output. Historical cache paths in
audit inventories remain references only. If prohibited embedded material is
found, omit it explicitly and record the original hash/transformation; do not
claim byte-identical preservation after redaction.

## Identity and claim reconciliation

Every source ID gets one recorded disposition. Existing matching entities retain
their legacy `/peptides/` route; genuinely new entities use `/library/` routes.
The completed mapping has 44 legacy attachments and 166 new entries: 245
canonical entities. Keep source IDs even across differing source kinds. Never
merge solely by name or suffix. The final count reflects identity adjudication,
not simply 79 + 210.

Keep molecule/fragment, ester, formulation, route and DAC/no-DAC distinctions.
Do not equate a premixed product to a community stack. Ambiguous matches remain
separate and related, with uncertainty visible.

Exact citation/claim duplicates may consolidate only while retaining original
titles, URLs, field locations and all source associations. Same-paper protocols
with differing populations, regimens, durations or outcomes remain separate.
Never average dose/PK ranges or choose the newest/longest claim automatically.
Any resolution needs a recorded reason and citations.

Required conflict fixtures include the wiki's approximately 40-minute in-vitro
BPC-157 half-life versus the source template's 4-6-hour range; TB-500 full
molecule/fragment ambiguity; CJC with/without DAC; and the legacy BPC/TB stack's
contradictory statements about whether a combination study exists.
Keep circular wiki backlinks attributed, not independent corroboration.

## Public reading experience

Retain artifactkit and extend the directory to all kinds without removing benefit
browsing. Hierarchy: identity/kind, overview, separate regulatory/evidence labels,
research/verdict, study protocols, community descriptions/negative findings,
uncertainty/conflicts/provenance and citations/related entries.

Each study protocol retains population, regimen, duration, outcome and source.
Community descriptions have their own citations and remain separate from study
evidence. A bounded empty finding means no suitable account was verified in the
dated checks, not that the practice does not exist. Missing, empty and explicitly
researched-empty states must be distinguishable.

Show source uncertainty and evidence categories without implying human efficacy,
current approval or safety. Source tiers are not a numerical ranking or a direct
mapping to legacy status colours. Preserve null values and original optional
metadata. No combined recommended protocol may be synthesised.

Use a positive public-field allowlist. Do not expose template objects/defaults
in HTML, embedded JSON, search or public exports. Only approved sourced PK context
may project out of a template, retaining ranges/source notes/uncertainty/conflicts.
Retain old favorite keys and `pw_favorites`; add a distinct new-entity namespace.

Brand headers/titles/home/about/docs and machine site names Biohacker Wiki.
Keep technically correct peptide-specific labels and existing repository links.
Make canonical URLs, breadcrumbs, search actions, favorites, sitemap and llms.txt
work under the unchanged `/peptide-wiki/` base. Keep legacy JSON endpoints
compatible and add a broad public catalogue export. Do not mark practices as drugs.
Any local app project-display rename must use supported tooling or be handed off
as a manual step; never alter app databases/folders implicitly.

## Historical checks and publication gate

Retain 2026-10-06 ledger dates as historical checks. Build/import time is not
review time. Fresh review records must separately record URL/identity, date,
availability, claim match, population, suitability and result. HTTP 200 or quote
matching alone does not verify a claim.

Before any future republication, require fresh suitability/rights checks and
separate user permission. Local migration can preserve explicitly historical or
unverified content, but must not claim release readiness or fresh verification.

## Acceptance criteria

1. Preserve all 79/8/8 legacy records, text, citations, routes, endpoints and favorite identities.
2. Account for all 210 source IDs and reconcile all 543/270/163 original link/protocol/community occurrences, including shared and circular sources.
3. Preserve all 130 ledger outcomes, their dates and bounded meanings (59 verified, 71 empty).
4. Retain the requested tracked audit material with path/hash/status, never in public articles, indexes, counts, exports or deploy output.
5. Round-trip every authored field/template/PK range/blend and enforce the confirmed rendering restrictions.
6. Deduplicate exact identities without losing attribution; keep distinct variants/protocols/conflicts distinguishable.
7. Apply Biohacker Wiki branding without changing repository or public URL.
8. Build offline without source/Swift; import deterministically and idempotently, validating before mutation and reporting actionable errors.
9. Preserve all old routes and correct base-path links; enumerate intended public pages in machine outputs, never audit content.
10. Reach every kind through discovery; old/new favorites and related/variant links work.
11. Verify mobile/tablet/desktop, light/dark, keyboard, long/empty/conflict states with screenshots.
12. Introduce no source mutation, private/publisher material, publication, unapproved recommendations or template-derived calculator autofill.

## Verification

Start each task with a failing behavioural test. Use stdlib tests and HTML parsing
before considering new tooling. Reconcile complete source locations/hashes/IDs,
not just aggregate counts. Hand-trace BPC-157, caffeine/sleep, one empty finding
and one rejected draft.

Adversarial cases: duplicate keys/IDs, omitted/unknown fields, unsafe URL schemes
and traversal, source drift, partial writes, ambiguous variants, different
same-paper protocols, null/missing/empty values, Unicode/long text, script-closing
strings, archive leakage, absent source/Swift and repeated imports.

Check browser flows at 375/768/1440 CSS pixels, light/dark, keyboard/menu/search,
old/new favorites, no-results and conflict states. Test local HTTP root and the
Pages subpath; preserve documented file-open behaviour with its cookie limits.
The existing calculator must remain unchanged and unfilled by imported defaults.
Record actual commands, results, screenshots and skipped checks. The initial
sprint-stop boundary was superseded by explicit user-directed autonomous
continuation. The completed local evidence is in [the plan](../PLAN.md).
