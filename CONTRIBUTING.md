# Contributing

Corrections and additions welcome. This is a community reference, not a personal blog — if you know something's wrong or missing, fix it.

## What's useful

- Correcting a dosing range, half-life, or mechanism description that's inaccurate.
- Adding a citation for a claim that currently has none.
- Adding a peptide that's missing, with the same fields as existing entries.
- Fixing a broken cross-link or a typo.
- Flagging a safety note that's outdated or wrong.

## What's not

- Sourcing claims from vendor marketing copy or forum anecdotes presented as fact. Cite a study, a review, or say plainly it's community-reported and unverified.
- Naming or linking specific vendors anywhere in the content. This is a reference site, not a storefront directory.
- Dosing advice framed as a recommendation rather than "here's what's reported." This site describes what people do and what evidence exists — it doesn't tell anyone what to do.

## How

1. Fork the repo.
2. Edit `peptides.json`, `categories.json`, or `stacks.json` directly. Don't hand-edit anything in `out/` — it's generated.
3. Run `python3 generate.py` and check your change rendered correctly.
4. Open a PR describing what changed and why. Link a source if you're correcting a factual claim.

## Preserved Biometra research

`research/biometra/` is a source-pinned migration bundle, not another set of
editable peptide articles. Its manifest records authority and original hashes.
Do not hand-edit imported files, promote intermediate/rejected audit drafts into
accepted claims, or copy the archive into generated output.

App templates/default doses/schedules stay archived; they must not become
recommendations or calculator autofill. Keep study protocols, community accounts,
uncertainty and differing claims separate. Historical checks do not establish
current validity or publication suitability.

Run `python3 -B -m unittest discover -s tests` before the normal build.
Identity changes belong in `research/mapping.json`, with an explicit reason.
Every source ID must have exactly one disposition. Keep uncertain variants
separate and related. Do not merge protocols from different populations,
collapse contradictory claims or count wiki-origin backlinks as independent
corroboration. The complete public-field projection lives in `library.py`.

The legacy JSON exports, URLs and favorite keys are compatibility contracts.
Adding broader entries must not remove them. Change generated routes, search,
favorites and machine outputs together, and extend behavioural tests.

See [docs/PLAN.md](docs/PLAN.md) for the completed scope and actual verification.
The [README](README.md#checks) documents optional screenshot/browser checks.
Normal builds remain offline and Python-only. Fresh source-suitability/rights
checks and owner permission are required before any new public republication;
import/build success is not publication approval.

## Style

Keep entries compact. Say the thing directly — no hedging, no filler, no "it's important to note." If evidence is weak or the compound is unstudied in humans, say that plainly instead of padding around it.
