# B-82 research pack

Research snapshot: 2026-10-06. Source application commit: `85446ce`.

The original queue contains 130 non-peptide/hormone catalogue entries. There are
59 accepted descriptions and 71 researched-empty outcomes. Empty means no suitable
description was verified in the recorded checks, not that no practice exists.
These descriptions are not recommendations or evidence of safety or effectiveness.

## Reuse in another project

Copy this directory's tracked files. Start with `catalogue-evidence.json` and
`research-outcomes.json`: these are self-contained snapshots of the final catalogue
data and the per-entry audit ledger. Catalogue identifiers are retained as stable
keys; another project can map them to its own identifiers.

The application still uses `scripts/evidence/evidence.json` and
`scripts/evidence/community-research.json`. This pack is a dated research snapshot,
not a second editable source of application data.

## Material retained

| File | Meaning |
| --- | --- |
| `catalogue-evidence.json` | Final evidence and community data for all 130 entries |
| `research-outcomes.json` | Dated checks, accepted citations and bounded empty outcomes |
| `candidate-research.json` | Researcher's proposals, searches and attempted URLs; not publication approval |
| `working-editorial-review.json` | Intermediate rewrites and rejection reasons, before final verification |
| `existing-description-review.json` | Independent review notes for the original 19 descriptions |
| `publication-overrides.json` | Corrected nap/caffeine descriptions and the two NIH traditional-use additions |
| `source-fetch-index.json` | Retrieval status and cache locations; quote matching is not verification |
| `fetch_sources.py` | Original source-fetch helper; accepts a candidate JSON and an output directory |
| `offline-inventory.json` | File hashes and checksum of the complete local archive |

Proposals may contain rejected claims. The final ledger and catalogue snapshot,
not an intermediate proposal or a successful HTTP response, determine what was
accepted. Recheck live pages and suitability before publishing in another project.
No new drug doses or recommendations were imported.

## Complete offline archive

`local-only/research-materials-full.tar.gz` retains every available B-82 session artefact:
cached HTML and extracted text, source metadata, original candidates and source
excerpts, working notes, scripts, logs, screenshots and the available temporary
review reports, plus the recorded source-retrieval requests and results. No
conversation instructions are exported. It also contains snapshots of the final evidence, ledger,
generator, tests, generated Swift, backlog and decisions. The archive's manifest
records individual file hashes; `offline-inventory.json` records the archive hash.

Raw publisher pages and excerpts are deliberately **gitignored and not pushed**.
The tracked pack preserves original research notes, data and provenance, not
copies of third-party articles. Retaining a cache does not grant republication
rights. Original session artefacts are left untouched.

The archive is currently inside this worktree, with a second copy in this session's
artefact directory. Copy it to durable storage before
archiving or deleting the session; deleting the worktree can remove ignored files.
No permission was available to write a permanent archive outside the project.
This preserves available files, not intermediate versions that were overwritten
before this preservation step.
