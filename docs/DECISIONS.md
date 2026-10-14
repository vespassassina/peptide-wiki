# Decisions

## 2026-10-14 Map exact identities without resolving clinical disagreements

The user authorised autonomous completion of the remaining approved scope,
superseding the initial Sprint 1 stop boundary. Publication, push, PR and source
mutation remain out of scope.

Use an explicit reviewed disposition for every one of the 210 source IDs:
44 attach to existing identities and 166 become new entries, yielding 245
canonical entities. Keep TB-500 fragment and kisspeptin-10 separate from broader
legacy articles; keep a premixed CJC/ipamorelin product distinct from a stack.
Cross-kind matches retain their old peptide URLs and favorite keys.

Project only approved public fields. Keep exact source claims, original links,
historical outcomes and all occurrence provenance. Deduplicate exact claims and
PMID/DOI identities without removing original URLs, titles, null metadata or
differing study populations. Wiki-origin backlinks are circular, not independent
support. Preserve BPC-157 PK, TB-500 identity, CJC DAC and BPC/TB stack conflicts
explicitly; an attachment does not adjudicate them. No new dependency is needed
for this projection or the normal build.

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
