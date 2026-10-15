# Publication handoff

## Done

The local consolidation is complete through `ac57f27`, and the menu correction
is committed in `8377775`. The owner requested merge, push and publication and
then directed autonomous completion. The fresh historical-publication
suitability/rights review is now recorded; no clinical verification or waiver
of publisher rights is claimed.

Release preflight confirmed:

- The repository is public and its default branch is `main`.
- A push to `main` automatically deploys GitHub Pages.
- No pull request exists for this session branch.
- The latest successful deployment observed is the original baseline
  `5b66ac030272f1802aae4c0812eef6c3fdacb082`.
- All 37 Python tests passed, with no skips; `git diff --check` passed.

No merge, push or publication was performed.

The owner's follow-up menu request is complete locally in `8377775`. The mobile
navigation now opens on its own full-width row, scrolls vertically on short
screens, closes on Escape/outside clicks/focus exit, resets at the breakpoint,
and remains available without JavaScript. All 32 Python tests and the actual
277-page build passed. Chromium passed 18 menu cases plus the existing 12 full
flows; 18 screenshots and `results.json` are under session `files/menu-check/`.
Native-device/other-browser and published-site checks remain unperformed.

## Live review findings

The initial partial review is retained inside `research/publication-review.json`.
Five of 142 unique community-source URLs received live claim readings. The sleep-diary and
bounded traditional-use examples are supported in their limited contexts.
The simplified NIH extractor omitted the main article, so the full HTML was
parsed in memory instead; no publisher text was persisted.

The initial review identified a concrete source-support issue:
the DHEA account links a vendor product page, contrary to the target contribution
policy, and its additional 100 mg adjustment statement was not verified in the
current retrieved label. The current label supports the narrower daily-capsule
statement. This is a finding about source support, not medical dosing guidance.
Two IGF-1 LR3 claims also remain unverified; matching terms alone does
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

The fresh review now covers every imported entry and community account as
historical reference only. All 163 community descriptions were read; all 270
study population/source contexts and 210 uncertainty fields reconcile. Known
support, formulation, route, population and unit limitations are visible before
the affected original account wording. Unverified accounts are collapsed and
labelled as authored paraphrases, not quotations or medical guidance.

The approved lossless-citation scope resolves the vendor-policy conflict through
an explicit historical-provenance exception, not a vendor recommendation.
The owner's publication instruction covers the identified authored material;
publisher originals remain excluded and no third-party rights clearance is
invented.

All 888 registered citation URLs have dated availability dispositions:
660 HTML, 23 non-HTML, 57 HTTP errors, three request failures, three response
limits, 114 possible access barriers and 28 circular-provenance URLs. No access,
certificate or redirect barrier was bypassed. Builds fail on missing or
duplicate review coverage. Only allowlisted status metadata enters public data.

Final local evidence: 37 passing tests, actual offline Python-only build of 277
pages, all 18 menu cases and 12 complete Chromium flows passed. Twenty-two
screenshots and results are in session `files/release-check/`. Raw source bytes,
legacy JSON and CI remain unchanged; audit/default files are absent from output.

Commit the review/rendering follow-up, refresh remote ancestry, fast-forward
`main` without force, wait for Pages and verify the published site and excluded
paths. Remove this handoff after successful publication. No remaining source
claim is silently upgraded to clinically verified.

No server or browser-verification helper remains running. Optional Playwright
1.64.1 and Chromium remain in session `files/menu-tooling/` for release checks;
they are not repository dependencies. Screenshots and full local evidence are
referenced in `docs/PLAN.md`. Remove this handoff when publication is complete.
