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

The owner's follow-up menu request is complete locally in `8377775`. The mobile
navigation now opens on its own full-width row, scrolls vertically on short
screens, closes on Escape/outside clicks/focus exit, resets at the breakpoint,
and remains available without JavaScript. All 32 Python tests and the actual
277-page build passed. Chromium passed 18 menu cases plus the existing 12 full
flows; 18 screenshots and `results.json` are under session `files/menu-check/`.
Native-device/other-browser and published-site checks remain unperformed.

## Live review findings

A fresh partial review is recorded in `research/publication-review.json`.
Five of 142 unique community-source URLs received substantive examination. The sleep-diary and
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

Availability checks are now complete for all 142 unique community-source URLs,
covering 163 description locations. `research/community-live-checks.json`
records 139 retrieved HTML responses and three HTTP 403 responses:

- `https://muscleandbrawn.com/anabolics/testosterone-enanthate-cycle/`
- `https://muscleandbrawn.com/sarms/andarine-s4/`
- `https://www.cdc.gov/physical-activity-basics/guidelines/index.html`

No access barriers were bypassed. This report contains response identities,
titles, sizes and hashes, not publisher pages or excerpts. Every check remains
explicitly uncleared for claim matching and suitability; availability is not
approval. The report is excluded from the generated site. Its 142 unique URLs
and 163 claim locations were checked against the report, and the built output
still contains exactly 277 HTML pages with no research directory.

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

No server or browser-verification helper remains running. Optional Playwright
1.64.1 and Chromium remain in session `files/menu-tooling/` for release checks;
they are not repository dependencies. Screenshots and full local evidence are
referenced in `docs/PLAN.md`. Remove this handoff when publication is complete.
