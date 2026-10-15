# Publication handoff

## Done

The local consolidation is complete through `ac57f27`. On 2026-10-15 the owner
requested merge, push and publication. This authorises those operations, but
does not expressly waive the previously approved source-suitability and rights
review gate.

Release preflight confirmed:

- The repository is public and its default branch is `main`.
- A push to `main` automatically deploys GitHub Pages.
- No pull request exists for this session branch.
- The latest successful deployment observed is the original baseline
  `5b66ac030272f1802aae4c0812eef6c3fdacb082`.
- All 32 Python tests passed again, with no skips; `git diff --check` passed.

No merge, push or publication was performed.

## Live review findings

A fresh partial review is recorded in `research/publication-review.json`.
Five of 142 unique community-source URLs were examined. The sleep-diary and
bounded traditional-use examples are supported in their limited contexts.
The simplified NIH extractor omitted the main article, so the full HTML was
parsed in memory instead; no publisher text was persisted.

There is now a concrete publication issue, not merely an unchecked gate:
the DHEA account links a vendor product page, contrary to the target contribution
policy, and its additional 100 mg adjustment statement was not verified in the
current retrieved label. The current label supports the narrower daily-capsule
statement. This is a finding about source support, not medical dosing guidance.
Two IGF-1 LR3 account checks also remain uncleared; matching terms alone does
not validate the full claims or distinguish animal evidence from human use.

GitHub reports the source repository as private with no detected licence;
the target is public and MIT-licensed. The owner's instruction authorises the
publication operation, but target licensing does not establish rights in
third-party material. No blanket clearance or infringement finding is inferred
from the absent source licence. No publisher pages, images or excerpts have
been added.

## Blocked and next

The fresh suitability/rights review is not complete. The source audit README
requires live suitability checks before reuse in another project, and
`docs/specs/biohacker-wiki-consolidation.md` explicitly retains this release gate.
Historical checks and successful builds do not satisfy it.

The owner was asked whether to complete that review or explicitly waive the
gate for a labelled historical snapshot, but was unavailable. Do not infer a
waiver from that absence.

Complete and record the remaining review and resolve the identified source/
policy issues before proceeding, or obtain an
explicit owner decision changing the release policy without misrepresenting
rights or verification. Then check remote changes, merge and push using normal
non-destructive Git/GitHub operations, wait for Pages deployment and verify the
published site and audit/default exclusions. Never force-push `main`.

No server or browser-verification helper remains running. Prior screenshots and
full local evidence are referenced in `docs/PLAN.md`. Remove this handoff when
the publication task is complete.
