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

## Blocked and next

The fresh suitability/rights review is not complete. The source audit README
requires live suitability checks before reuse in another project, and
`docs/specs/biohacker-wiki-consolidation.md` explicitly retains this release gate.
Historical checks and successful builds do not satisfy it.

The owner was asked whether to complete that review or explicitly waive the
gate for a labelled historical snapshot, but was unavailable. Do not infer a
waiver from that absence.

Complete and record the required review before proceeding, or obtain an
explicit owner decision changing the release policy without misrepresenting
rights or verification. Then check remote changes, merge and push using normal
non-destructive Git/GitHub operations, wait for Pages deployment and verify the
published site and audit/default exclusions. Never force-push `main`.

No server or browser-verification helper remains running. Prior screenshots and
full local evidence are referenced in `docs/PLAN.md`. Remove this handoff when
the publication task is complete.
