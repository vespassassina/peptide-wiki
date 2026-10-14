# Decisions

## 2026-10-14 Preserve Biometra research before changing the site

Import the pinned canonical evidence and final B-82 ledger, with the user-selected
tracked intermediate/rejected research pack in a non-deployed audit archive.
Keep all 210 authored catalogue entries, including original links and every
template field. Do not publish the archive or interpret rejected drafts as claims.
Normal site builds remain Python-only and do not access the source checkout.

The full authored export comes from scratch copies of pure Foundation domain
sources, exposing only the copied private accessor. Exporting builtInEntries
would lose authored links because it applies generated evidence overlays.
Preserve the original Swift file and hashes of every compilation input.

Swift Set encoding made real reimports nondeterministic. Sort only the encoded
weekday Set, then decode and compare every complete entry to the original value.
Do not sort arbitrary arrays or infer defaults. Optional null source-author
metadata in canonical evidence remains null, not silently dropped.

No third-party packages were added. Migration requires Python and a Swift 6
compiler; ordinary site generation needs only Python. Use stdlib unittest for
preservation, validation, round-trip and adversarial checks.

Site branding only will change to Biohacker Wiki in a later approved sprint;
the repository and public URL stay unchanged. Archive app defaults rather than
rendering recommendations or autofilling the calculator. Source-to-wiki links
are circular provenance. Fresh republication suitability/rights review remains
a separate gate, not something an import or successful URL fetch establishes.
