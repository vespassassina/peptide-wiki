# Peptide Wiki

**Live site: https://vespassassina.github.io/peptide-wiki/**

A static reference site for research peptides: mechanism, dosing protocols reported in the community, safety notes, and citations. 72 peptides across 8 categories, plus 8 common stacks.

This is not medical advice. Most of these compounds are unregulated, sold for research use only, and have thin or no human trial data. The site says so on every page. Read it as a research summary, not a green light.

## What's here

- `peptides.json`, `categories.json`, `stacks.json` — the actual content.
- `generate.py` — builds the static HTML site from those three files.
- `vendor/artifactkit/` — the CSS/JS design system the site is built on.
- `out/` — build output (gitignored, generated locally).

## Building the site

Needs Python 3, no dependencies.

```
python3 generate.py
```

Output lands in `out/`. Open `out/index.html` directly in a browser, or serve the folder (`python3 -m http.server -d out`) — some features, like the favorites list, need a real HTTP origin to work properly (browsers isolate cookies per `file://` page).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: fix a dosing number, add a missing citation, correct a mechanism description, or add a peptide that's missing. Open a PR against the JSON files, not the generated HTML.

## Structure of an entry

Each peptide in `peptides.json` has: name, aliases, categories, status (research-only, prescription, etc.), origin, mechanism, reported benefits, dosing protocols as reported by the community, side effects, safety notes, citations, and related peptides. Look at an existing entry before adding a new one — consistency matters more than creativity here.

## License

MIT. See [LICENSE](LICENSE). Content is provided as-is — verify anything before acting on it.
