# Biohacker Wiki consolidation handoff

## Done

Sprint 1 is complete. The approved scope covers five sprints, but only Sprint 1
was authorised. The site still renders the original peptide library; broad
research pages and Biohacker Wiki branding are not implemented yet.

The source-pinned bundle preserves all 210 authored entries, canonical evidence,
the final 130-entry community ledger, original authored Swift and the requested
tracked B-82 audit pack. The 15 files total approximately 2 MB. The manifest
records original paths/hashes, classifications, compile inputs, counts and
export transformations. All audit content and app defaults remain outside
generated/deploy output.

The exporter compiles scratch copies, not the source checkout. It exports
authoredEntries, preserving original links before runtime overlays. It sorts only
the weekday Set representation, then verifies complete Codable equality. Actual
reimport caught and fixed Swift's otherwise nondeterministic Set encoding.
Explicit null author metadata in canonical research remains preserved.

No legacy JSON, generator, CSS, CI, remote URL or source file was changed.
No push, PR or publication occurred.

## Evidence

- `python3 -B -m unittest discover -s tests`: 17 tests passed, no skips with Swift available.
- `python3 -B generate.py`: 103 HTML pages, preserving 79 peptides, 8 stacks and 8 categories.
- Actual import followed by repeated `--write`: second run reported `Already identical`.
- Counts reconciled: 210 records, 543 top-level links, 270 study protocols, 163 community descriptions, 210 verdicts and 130 final ledger outcomes (59 verified, 71 bounded empty).
- Thirty wiki backlinks retained as circular provenance, not independent evidence.
- Actual CLI with this target repo as the wrong source failed on the pinned commit; all 15 bundle file hashes remained unchanged.
- Hostile duplicate keys/IDs, unsafe paths/symlinks/URLs, missing/unknown fields, malformed shapes, bad ledger dates/statuses, count mismatches and existing-bundle conflicts were rejected in tests.
- Original data hashes, all legacy routes/exports/favorite keys and current relationships passed preservation checks.
- Deploy output contains no research/audit directory or imported catalogue pages.
- Source working tree remained clean; `git diff --check` passed.

Hand-traced source examples: BPC-157 preserves original ClinicalTrials.gov links
and its 4-6-hour template range, separate from the legacy approximately 40-minute
claim; sleep retains its attributed practice; paracetamol retains the dated,
bounded empty outcome; extended-fast's commercial-source rejection remains
labelled `reject` in the audit pack.

Skipped deliberately: new UI/browser screenshots and flows, identity adjudication,
rendering, branding, fresh live source/rights verification and deployment.
These belong to later sprints or a separately permissioned publication gate.
No medical or publication-suitability verification is claimed.

## Next and blocked

Sprint 2 needs user approval. Map every source ID to an explicit canonical entity
or separate related variant, then reconcile attributed evidence/conflicts.
Do not merge by suffix/name alone, collapse different study populations, turn
templates into advice or count source-to-wiki links as independent corroboration.

Use [PLAN.md](PLAN.md) and the
[specification](specs/biohacker-wiki-consolidation.md). Known conflict fixtures
include BPC-157 PK, TB-500 molecule/fragment identity, CJC DAC/no-DAC and conflicting
legacy BPC/TB stack wording. Cross-kind entities such as hCG and teriparatide
already have legacy peptide routes that must remain stable.

All future public projections need an explicit field allowlist. Do not copy
`research/biometra/` into `out/`, and do not expose template objects in embedded
JSON or public data. Historical checks stay dated; no reviewed-today stamps.

## Resume

Run the tests and normal Python build above; neither the archive checks nor site
generation requires the source checkout. Swift is needed for exporter tests
(explicitly skipped when unavailable) and actual re-export only.

To verify the import against the approved isolated source worktree:

```sh
python3 -B scripts/import_biometra.py \
  --source /absolute/path/to/approved/biometra-worktree --write
```

The source must still be at `adc7684614f9439b41d91a3312b62e7982c7e20e`.
An identical import is a no-op; a differing existing bundle is rejected for
review, never silently overwritten. Do not use the main source checkout.
After approval, begin Sprint 2 with failing behavioural tests and update the
tracked plan/decisions. Delete this handoff only when the consolidation is done.
