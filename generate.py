#!/usr/bin/env python3
"""Build Biohacker Wiki from preserved legacy data and pinned Biometra research."""
import json, os, html, shutil, re, sys, tempfile
from datetime import date
from pathlib import Path
from library import load_library, KIND_LABELS, TIER_LABELS
from scripts.import_biometra import ImportFailure

SITE_DOMAIN = "https://vespassassina.github.io/peptide-wiki"
FAVICON = ('<link rel="icon" href="data:image/svg+xml,'
           '%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22%3E'
           '%3Ctext y=%22.9em%22 font-size=%2280%22%3E%F0%9F%A7%AC%3C/text%3E%3C/svg%3E">')

def relativize_links(out_path, content):
    """Rewrite root-relative href/src/action ("/x/y.html") into paths relative to
    out_path, so the site works when opened straight off disk via file://."""
    depth = out_path.count("/")
    prefix = "../" * depth
    def repl(m):
        attr, url = m.group(1), m.group(2)
        return f'{attr}="{prefix}{url.lstrip("/")}"'
    return re.sub(r'(href|src|action)="(/[^"]*)"', repl, content)

SRC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SRC, "out")
VENDOR = os.path.join(SRC, "vendor", "artifactkit")

with open(os.path.join(SRC, "peptides.json")) as f:
    PEPTIDES = json.load(f)
with open(os.path.join(SRC, "categories.json")) as f:
    CATEGORIES = json.load(f)
with open(os.path.join(SRC, "stacks.json")) as f:
    STACKS = json.load(f)

TODAY = date.today().isoformat()
SITE_NAME = "Biohacker Wiki"
SITE_DESC = "A source-attributed reference on peptides, medications, supplements, food, exercise and recovery. Read what was studied, what people report, and what remains uncertain."
LIBRARY = None

def script_json(value):
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

# custom line icons per category, replacing plain emoji. viewBox 0 0 24 24,
# sized and colored via CSS (currentColor / .cat-icon*).
CATEGORY_ICON_SVG = {
    "recovery-healing": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="9" width="18" height="6" rx="3" transform="rotate(-45 12 12)"/><circle cx="9" cy="12" r="1" fill="currentColor" stroke="none" transform="rotate(-45 12 12)"/><circle cx="15" cy="12" r="1" fill="currentColor" stroke="none" transform="rotate(-45 12 12)"/></svg>',
    "anti-aging": '<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M12 2 L14.2 9 L21 11 L14.2 13 L12 20 L9.8 13 L3 11 L9.8 9 Z"/></svg>',
    "longevity": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h12M6 21h12M7 3c0 5 4 6 5 9-1 3-5 4-5 9M17 3c0 5-4 6-5 9 1 3 5 4 5 9"/></svg>',
    "fat-loss": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l6 6 3-3 9 9"/><path d="M21 11v6h-6"/></svg>',
    "fitness-muscle": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 10v4M4 9v6M20 9v6M22 10v4M7 12h10"/><rect x="4.5" y="7" width="3" height="10" rx="1"/><rect x="16.5" y="7" width="3" height="10" rx="1"/></svg>',
    "sexual-health": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20s-7.5-4.6-10-9.3C.5 7.4 2.2 4 5.7 4c2 0 3.6 1.1 4.3 2.7C10.7 5.1 12.3 4 14.3 4c3.5 0 5.2 3.4 3.7 6.7C15.5 15.4 12 20 12 20z"/></svg>',
    "nootropics-cognitive": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 4a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3 3 0 0 0 2 5h1a3 3 0 0 0 3-3V6a2 2 0 0 0-1-2z"/><path d="M15 4a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3 3 0 0 1-2 5h-1a3 3 0 0 1-3-3V6a2 2 0 0 1 1-2z"/><path d="M12 6v12"/></svg>',
    "bioregulators": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3c0 6 12 12 12 18M18 3c0 6-12 12-12 18"/><path d="M7.5 8h9M6.5 12h11M7.5 16h9"/></svg>',
}
# hue for each category's homepage card background (see .cat-card in site.css)
CATEGORY_HUE = {
    "recovery-healing": 200, "anti-aging": 320, "longevity": 45, "fat-loss": 160,
    "fitness-muscle": 15, "sexual-health": 350, "nootropics-cognitive": 265, "bioregulators": 185,
}

def cat_icon(cslug, cls="cat-icon"):
    svg = CATEGORY_ICON_SVG.get(cslug, "")
    return f'<span class="{cls}" aria-hidden="true">{svg}</span>'

def esc(s):
    return html.escape(str(s), quote=True)

CAT_PEPTIDES = {c: [] for c in CATEGORIES}
for slug, p in PEPTIDES.items():
    for c in p["categories"]:
        CAT_PEPTIDES.setdefault(c, []).append(slug)
for c in CAT_PEPTIDES:
    CAT_PEPTIDES[c].sort(key=lambda s: PEPTIDES[s]["name"].lower())

ALL_SLUGS = sorted(PEPTIDES.keys(), key=lambda s: PEPTIDES[s]["name"].lower())
ALL_STACK_SLUGS = sorted(STACKS.keys())

# peptide slug -> list of stack slugs that include it, for cross-linking from leaf pages
PEPTIDE_STACKS = {}
for sslug, s in STACKS.items():
    for comp in s["component_slugs"]:
        PEPTIDE_STACKS.setdefault(comp, []).append(sslug)

# status -> (pill class, short label). Hand-classified for accuracy rather than
# pattern-matched, since evidence tier is the single most important signal on this site.
STATUS_TIER = {
    "bpc-157": ("ak-pill-off", "Research chemical"),
    "tb-500": ("ak-pill-off", "Research chemical"),
    "kpv": ("ak-pill-off", "Research chemical"),
    "ara-290": ("ak-pill-warn", "Investigational (trialed)"),
    "ghk-cu": ("ak-pill-info", "Cosmetic (topical) / off-label injectable"),
    "epithalon": ("ak-pill-off", "Research chemical"),
    "thymosin-alpha-1": ("ak-pill-ok", "Approved abroad (Rx)"),
    "nad": ("ak-pill-off", "Unregulated / not a peptide"),
    "mots-c": ("ak-pill-off", "Research chemical"),
    "humanin": ("ak-pill-off", "Research chemical"),
    "semaglutide": ("ak-pill-ok", "FDA-approved"),
    "tirzepatide": ("ak-pill-ok", "FDA-approved"),
    "retatrutide": ("ak-pill-warn", "Investigational (Phase 3)"),
    "aod-9604": ("ak-pill-risk", "Failed efficacy trial"),
    "tesamorelin": ("ak-pill-ok", "FDA-approved"),
    "cjc-1295": ("ak-pill-off", "Research chemical"),
    "ipamorelin": ("ak-pill-off", "Research chemical"),
    "sermorelin": ("ak-pill-info", "Formerly FDA-approved"),
    "mk-677": ("ak-pill-risk", "Discontinued (safety signal)"),
    "igf-1-lr3": ("ak-pill-risk", "Research chemical (acute risk)"),
    "pt-141": ("ak-pill-ok", "FDA-approved (women's HSDD)"),
    "oxytocin": ("ak-pill-ok", "FDA-approved (obstetric use)"),
    "kisspeptin": ("ak-pill-warn", "Investigational"),
    "semax": ("ak-pill-info", "Approved in Russia"),
    "selank": ("ak-pill-info", "Approved in Russia"),
    "dsip": ("ak-pill-off", "Research chemical"),
    # --- expansion batch: 46 additional peptides added alongside the bioregulators
    # category and stack pages (see wiki_src/research/) ---
    "cagrilintide": ("ak-pill-warn", "Investigational (Phase 3)"),
    "mazdutide": ("ak-pill-warn", "Investigational (Phase 3)"),
    "survodutide": ("ak-pill-warn", "Investigational (Phase 3)"),
    "liraglutide": ("ak-pill-ok", "FDA-approved (2014 for diabetes, 2016 for weight loss)"),
    "adipotide": ("ak-pill-risk", "Discontinued (Phase 1 nephrotoxicity)"),
    "aicar": ("ak-pill-off", "Research chemical"),
    "5-amino-1mq": ("ak-pill-off", "Research chemical"),
    "hgh-somatropin": ("ak-pill-ok", "FDA-approved (GHD treatment)"),
    "ghrp-2": ("ak-pill-info", "Research compound"),
    "ghrp-6": ("ak-pill-info", "Research compound"),
    "hexarelin": ("ak-pill-info", "Research compound"),
    "cjc-1295-dac": ("ak-pill-info", "Research compound"),
    "mgf": ("ak-pill-info", "Research compound"),
    "ace-031": ("ak-pill-risk", "Investigational (halted clinical trials)"),
    "mt-2": ("ak-pill-risk", "Research chemical"),
    "mt-1": ("ak-pill-ok", "FDA approved (2019, USA)"),
    "gonadorelin": ("ak-pill-ok", "FDA approved"),
    "hcg": ("ak-pill-ok", "FDA approved"),
    "ss-31": ("ak-pill-info", "FDA Accelerated Approval (2025) for Barth Syndrome"),
    "foxo4-dri": ("ak-pill-warn", "Research compound"),
    "ahk-cu": ("ak-pill-warn", "Cosmetic ingredient (topical, unregulated as drug)"),
    "snap-8": ("ak-pill-info", "Cosmetic ingredient (topical, unregulated as drug)"),
    "matrixyl": ("ak-pill-info", "Cosmetic ingredient (topical, unregulated as drug)"),
    "ptd-dbm": ("ak-pill-warn", "Research chemical"),
    "ll-37": ("ak-pill-info", "FDA Category 1 bulk drug (compounding-pharmacy use only)"),
    "vip": ("ak-pill-warn", "FDA investigational (synthetic aviptadil had Fast Track status for COVID-19, not approved)"),
    "teriparatide": ("ak-pill-ok", "FDA-approved for osteoporosis"),
    "cerebrolysin": ("ak-pill-info", "Approved in 40+ countries; not FDA-approved in US"),
    "pe-22-28": ("ak-pill-off", "Research chemical"),
    "p21": ("ak-pill-warn", "Investigational research compound"),
    "pnc27": ("ak-pill-risk", "Preclinical oncology research only"),
    "thymalin": ("ak-pill-info", "Approved in Russia and Eastern Europe"),
    "vilon": ("ak-pill-info", "Available in Russia and some Eastern European countries"),
    "pinealon": ("ak-pill-info", "Available in Russia and some international suppliers"),
    "testagen": ("ak-pill-warn", "Experimental research compound"),
    "bronchogen": ("ak-pill-info", "Approved in Russia"),
    "cardiogen": ("ak-pill-info", "Approved in Russia"),
    "cortagen": ("ak-pill-info", "Approved in Russia"),
    "livagen": ("ak-pill-info", "Approved in Russia"),
    "pancragen": ("ak-pill-info", "Approved in Russia"),
    "prostamax": ("ak-pill-info", "Approved in Russia"),
    "cartalax": ("ak-pill-info", "Approved in Russia; research compound"),
    "chonluten": ("ak-pill-info", "Approved in Russia; research compound"),
    "crystagen": ("ak-pill-info", "Approved in Russia; limited Western literature"),
    "ovagen": ("ak-pill-info", "Approved in Russia; veterinary research applications documented"),
    "vesugen": ("ak-pill-info", "Approved in Russia; PubMed-indexed research available"),
}

def tier(slug):
    return STATUS_TIER.get(slug, ("ak-pill-off", "Research chemical"))

# ---------- shared chrome ----------
def site_nav(active=""):
    def cur(key):
        return ' aria-current="page"' if active == key else ""
    return f'''<header class="site-topbar" role="banner">
  <div class="site-topbar-inner">
    <a class="site-brand" href="/index.html"><span aria-hidden="true">🧬</span> {esc(SITE_NAME)}</a>
    <button class="site-nav-toggle" id="navToggle" aria-expanded="false" aria-controls="siteNav">Menu</button>
    <nav class="site-nav" id="siteNav" aria-label="Primary">
      <ul class="site-links">
        <li><a href="/index.html"{cur("home")}>Home</a></li>
        <li><a href="/directory.html"{cur("directory")}>Directory</a></li>
        <li><a href="/stacks.html"{cur("stacks")}>Stacks</a></li>
        <li><a href="/favorites.html"{cur("favorites")}>★ Favorites</a></li>
        <li><a href="/glossary.html"{cur("glossary")}>Glossary</a></li>
        <li><a href="/dosing-safety.html"{cur("dosing-safety")}>Dosing &amp; safety</a></li>
        <li><a href="/calculator.html"{cur("calculator")}>Calculator</a></li>
        <li><a href="/about.html"{cur("about")}>About</a></li>
      </ul>
      <form class="site-search" role="search" action="/directory.html" method="get">
        <label for="topSearch" class="visually-hidden">Search the library</label>
        <input class="ak-input" type="search" id="topSearch" name="q" placeholder="Search the library…" autocomplete="off">
        <button class="ak-btn" type="submit">Search</button>
      </form>
    </nav>
  </div>
</header>'''

def site_footer():
    return f'''<footer class="ak-footer">
  <p><strong>Not medical advice.</strong> This wiki summarizes published research, regulatory status and self-reported community experience for informational purposes only. Many compounds described here are unapproved research chemicals with limited or no human safety data. Consult a licensed physician before starting, stopping or combining any of these substances. See <a href="/about.html">about &amp; disclaimer</a>.</p>
  <p class="ak-small">Built {TODAY}; historical research is not newly verified. Biometra checks dated 2026-10-06 retain their original scope. · styled with <a href="https://github.com/vespassassina/artifactkit">artifactkit</a> · <a href="/data/library.json">full library data</a> · <a href="/data/peptides.json">legacy peptide data</a> · <a href="/sitemap.xml">sitemap</a> · <a href="/llms.txt">llms.txt</a></p>
</footer>'''

def breadcrumbs(items):
    lis, ld_items = [], []
    for i, (label, href) in enumerate(items, start=1):
        if href:
            lis.append(f'<li><a href="{esc(href)}">{esc(label)}</a></li>')
        else:
            lis.append(f'<li aria-current="page">{esc(label)}</li>')
        ld_items.append({"@type": "ListItem", "position": i, "name": label, **({"item": SITE_DOMAIN + href} if href else {})})
    ld = script_json({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": ld_items})
    return f'<ol class="ak-breadcrumb">{"".join(lis)}</ol>\n<script type="application/ld+json">{ld}</script>'

def page(title, description, active, body, canonical="", page_id="page", extra_scripts=""):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title if title == SITE_NAME else title + " · " + SITE_NAME)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(SITE_DOMAIN + canonical)}">
{FAVICON}
<link rel="stylesheet" href="/assets/theme.css">
<link rel="stylesheet" href="/assets/components.css">
<link rel="stylesheet" href="/assets/site.css">
<link rel="stylesheet" href="/assets/print.css">
</head>
<body>
<a class="ak-vh" href="#main">Skip to content</a>
{site_nav(active)}
<div class="ak-wrap" id="main">
{body}
</div>
{site_footer()}
<script src="/assets/core.js"></script>
<script src="/assets/site.js"></script>
<script>ak.init({{ id: "peptide-wiki-{esc(page_id)}", title: {script_json(title)} }});</script>
{extra_scripts}
</body>
</html>'''

# ---------- peptide leaf pages ----------
def pill(slug):
    cls, label = tier(slug)
    return f'<span class="ak-pill {cls}">{esc(label)}</span>'

def category_badges(cats):
    return "".join(f'<a class="ak-badge" href="/categories/{c}.html">{cat_icon(c, "cat-icon-sm")} {esc(CATEGORIES[c]["name"])}</a> ' for c in cats)

def fav_button(key, label):
    return f'<button type="button" class="ak-btn fav-toggle" data-fav-key="{esc(key)}" aria-pressed="false"><span class="fav-star" aria-hidden="true">☆</span> <span class="fav-label">Add to favorites</span></button>'

def related_list(keys):
    items = [
        f'<li><a href="{esc(LIBRARY["entries"][key]["path"])}" rel="related">{esc(LIBRARY["entries"][key]["title"])}</a></li>'
        for key in keys
    ]
    return f'<ul class="chip-list">{"".join(items)}</ul>' if items else "<p class=\"ak-small\">None listed.</p>"

def dosing_table(protocols):
    rows = "".join(f'<tr><td>{esc(d["route"])}</td><td>{esc(d["protocol"])}</td></tr>' for d in protocols)
    return f'''<div class="ak-tblwrap"><table class="ak-table">
<caption class="ak-vh">Reported dosing protocols</caption>
<thead><tr><th scope="col">Route</th><th scope="col">Reported protocol</th></tr></thead>
<tbody>{rows}</tbody></table></div>'''

def ul(items):
    return "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"

def citations_block(citations):
    if not citations:
        return '<p class="ak-small">No specific peer-reviewed citations indexed for this entry — see the research summary above for what evidence does exist.</p>'
    items = "".join(
        f'<li><a href="{esc(c["pubmed_url"])}" rel="noopener">{esc(c["title"])}</a> — <span class="ak-small">{esc(c["authors_year"])}</span></li>'
        for c in citations
    )
    return f'<ul class="citation-list">{items}</ul>'

def stack_chip_list(slugs):
    def label(s):
        aka = STACKS[s].get("aka")
        return f'{esc(STACKS[s]["title"])} ({esc(", ".join(aka))})' if aka else esc(STACKS[s]["title"])
    items = [f'<li><a href="/stacks/{s}.html" rel="related">{label(s)}</a></li>' for s in slugs if s in STACKS]
    return f'<ul class="chip-list">{"".join(items)}</ul>' if items else ""

def peptide_chip_list(slugs):
    items = [f'<li><a href="/peptides/{s}.html" rel="related">{esc(PEPTIDES[s]["name"])}</a></li>' for s in slugs if s in PEPTIDES]
    return f'<ul class="chip-list">{"".join(items)}</ul>' if items else '<p class="ak-small">None charted.</p>'

def mixing_block(p):
    m = p.get("mixing_notes")
    caution = p.get("mixing_caution")
    if not m and not caution:
        return ""
    parts = ['<p class="ak-small">Pulled from a community-charted mixing-compatibility reference (anecdotal, clinic-use, and community-reported signals) — not a safety guarantee. Verify independently before combining anything.</p>']
    if caution:
        parts.append(f'<div class="ak-banner"><strong>Note:</strong> {esc(caution)}</div>')
    if m:
        if m.get("clinic_combos"):
            parts.append(f'<h3>Used together in wellness-clinic protocols</h3>{peptide_chip_list(m["clinic_combos"])}')
        if m.get("anecdotal_combos"):
            parts.append(f'<h3>Anecdotally combined (outside clinic protocols)</h3>{peptide_chip_list(m["anecdotal_combos"])}')
        if m.get("reported_avoid"):
            parts.append(f'<h3>Reported as a combination to avoid</h3>{peptide_chip_list(m["reported_avoid"])}')
    return "".join(parts)

def conflict_block(entry):
    return "".join(
        f'<aside class="research-warning" role="note"><h2>Unresolved source difference</h2><p>{esc(item["text"])}</p><p class="ak-small">State: {esc(item["status"])} · Origins: {esc("; ".join(item["origins"]))}</p></aside>'
        for item in entry["conflicts"]
    )

def source_link(source):
    circular = source["url"].startswith("https://vespassassina.github.io/peptide-wiki/")
    note = ' <span class="ak-small">(wiki-origin reference; not independent corroboration)</span>' if circular else ""
    author = f' — {esc(source["author"])}' if source.get("author") else ""
    return f'<a href="{esc(source["url"])}" rel="noopener">{esc(source["title"])}</a>{author}{note}'

def research_block(entry):
    if not entry["research"]:
        return '<p class="ak-small">Legacy wiki record. No Biometra research attachment; absence is not a finding of no evidence.</p>'
    parts = ['<section class="ak-section research-section" id="biometra"><h2>Biometra research</h2><p class="research-status">Historical source snapshot. Not freshly verified, not a recommendation. Study findings, community accounts and app defaults are not interchangeable.</p>']
    if entry.get("legacy"):
        parts.append('<p>Legacy wiki wording and the source account below are preserved independently. Their claims may differ; attachment does not resolve disagreement or establish current approval.</p>')
    for research in entry["research"]:
        verdict = research["verdict"]
        parts += [
            f'<h3>{esc(research["title"])}</h3><p>{esc(research["summary"])}</p>',
            f'<p><strong>Evidence category:</strong> {esc(TIER_LABELS[research["evidenceTier"]])}. This describes the source category, not approval or certainty.</p>',
            f'<p><strong>Regulatory statement in source:</strong> {esc(verdict.get("approvalStatus") or "Not separately recorded; do not infer approval from the evidence category.")}</p>',
            f'<p>{esc(research["evidenceSummary"])}</p>',
            f'<h3>What the source supports</h3>{ul(verdict["benefits"])}',
            f'<h3>Risks and limits</h3>{ul(verdict["risks"])}<p><strong>Source bottom line:</strong> {esc(verdict["bottomLine"])}</p>',
            f'<p class="research-status"><strong>Uncertainty:</strong> {esc(research["uncertainty"])}</p>',
            '<h3>Study protocols — reports, not instructions</h3>',
        ]
        for study in research["protocols"]:
            parts.append(f'''<article class="research-study">
<h4>{esc(study["population"])}</h4>
<dl><dt>Reported regimen</dt><dd>{esc(study["regimen"])}</dd><dt>Duration</dt><dd>{esc(study["duration"])}</dd><dt>Reported outcome</dt><dd>{esc(study["outcome"])}</dd><dt>Source</dt><dd>{source_link(study["source"])}</dd></dl>
<details><summary>Claim provenance</summary><p class="ak-small">{esc("; ".join(study["origins"]))}</p></details></article>''')
        if not research["protocols"]:
            parts.append('<p>No study protocol recorded in this snapshot. This does not establish that no study exists.</p>')
        parts.append('<h3>Community and practice descriptions</h3><p class="ak-small">Accounts of a practice are not evidence of safety or effectiveness.</p>')
        for community in research["community"]:
            parts.append(f'<blockquote class="research-account"><p>{esc(community["description"])}</p><p>{source_link(community["source"])}</p></blockquote>')
        finding = research["communityFinding"]
        if finding:
            parts.append(f'<details class="research-finding"><summary>Historical research outcome: {esc(finding["status"])} · {esc(finding["checkedOn"])}</summary><p>{esc(finding["notes"])}</p><ul>')
            for check in finding["checks"]:
                parts.append(f'<li><a href="{esc(check["url"])}" rel="noopener">{esc(check["url"])}</a>: {esc(check["outcome"])} — {esc(check["reason"])}</li>')
            parts.append('</ul></details>')
        elif not research["community"]:
            parts.append('<p>No community description recorded. This entry has no final B-82 outcome record; it is not a researched-empty finding.</p>')
        parts.append('<h3>Pharmacokinetic context</h3>')
        pk = research.get("pk")
        if pk:
            value = f'{pk["lowerHours"]:g}–{pk["upperHours"]:g}' if "lowerHours" in pk else f'{pk["hours"]:g}'
            parts.append(f'<p><strong>Historical half-life estimate: {esc(value)} hours.</strong> {esc(pk.get("source") or "No specific source note recorded.")} Population/route context and estimates may differ. This is not a schedule or a verified human dosing rule.</p>')
        else:
            parts.append('<p>No half-life recorded in this source snapshot. No value has been inferred.</p>')
        parts.append('<h3>Source references</h3><ul>')
        seen = set()
        for source in research["links"] + research["originalLinks"]:
            if (source["url"], source["title"]) not in seen:
                parts.append(f'<li>{source_link(source)}</li>')
                seen.add((source["url"], source["title"]))
        parts.append(f'</ul><details><summary>Snapshot provenance</summary><p>Source ID: {esc(research["id"])}. Commit: <code>{esc(research["sourceCommit"])}</code>. Review state: {esc(research["reviewState"])}. Authored links are retained separately from the canonical evidence links in the public data. App templates/defaults and rejected drafts are archived, not deployed.</p></details>')
    parts.append('</section>')
    return "".join(parts)

def library_page(entry):
    crumbs = breadcrumbs([("Home", "/index.html"), (KIND_LABELS[entry["kind"]], f'/kinds/{entry["kind"]}.html'), (entry["title"], None)])
    structured = script_json({"@context": "https://schema.org", "@type": "Article", "name": entry["title"], "description": entry["summary"], "url": SITE_DOMAIN + entry["path"]})
    body = f'''{crumbs}<article><header class="ak-pagehead"><div><h1>{esc(entry["title"])}</h1><p class="ak-lede">{esc(entry["summary"])}</p><p>{esc(KIND_LABELS[entry["kind"]])}</p></div><div class="ak-meta">{fav_button(entry["id"], entry["title"])}</div></header>
{conflict_block(entry)}<div class="ak-prose">{research_block(entry)}<section><h2>Related entries and components</h2>{related_list(entry["related"])}</section></div></article><script type="application/ld+json">{structured}</script>'''
    return page(entry["title"], entry["summary"], "", body, canonical=entry["path"], page_id=entry["id"].replace(":", "-"))

def kind_page(kind):
    members = [entry for entry in LIBRARY["entries"].values() if entry["kind"] == kind]
    members.sort(key=lambda entry: entry["title"].casefold())
    items = "".join(f'<li><a href="{esc(entry["path"])}">{esc(entry["title"])}</a><p>{esc(entry["summary"])}</p></li>' for entry in members)
    body = f'{breadcrumbs([("Home", "/index.html"), (KIND_LABELS[kind], None)])}<header class="ak-pagehead"><div><h1>{esc(KIND_LABELS[kind])}</h1><p class="ak-lede">{len(members)} source-attributed entries. Evidence and regulatory status vary; read each entry’s uncertainty.</p></div></header><ul class="research-index">{items}</ul>'
    return page(KIND_LABELS[kind], "Browse " + KIND_LABELS[kind].lower(), "directory", body, canonical=f"/kinds/{kind}.html", page_id="kind-" + kind)

def peptide_page(slug, p):
    cats = p["categories"]
    primary_cat = cats[0]
    aliases = ", ".join(p.get("aliases", [])) or "—"
    jsonld = script_json({
        "@context": "https://schema.org", "@type": "MedicalWebPage", "name": p["name"],
        "alternateName": p.get("aliases", []), "description": p["tagline"],
        "about": {"@type": "Drug", "name": p["name"], "alternateName": p.get("aliases", [])},
        "medicalAudience": "Patient",
    })
    crumbs = breadcrumbs([("Home", "/index.html"), (CATEGORIES[primary_cat]["name"], f"/categories/{primary_cat}.html"), (p["name"], None)])
    body = f'''{crumbs}
<article itemscope itemtype="https://schema.org/MedicalWebPage" data-peptide-slug="{esc(slug)}">
<header class="ak-pagehead">
  <div>
    <p class="ak-eyebrow">{esc(CATEGORIES[primary_cat]["name"])}</p>
    <h1 itemprop="name">{esc(p["name"])}</h1>
    <p class="ak-lede" itemprop="description">{esc(p["tagline"])}</p>
    <p class="peptide-pills">{pill(slug)} {category_badges(cats)}</p>
  </div>
  <div class="ak-meta">
    <span class="ak-asof">Historical reference · not reverified</span>
    {fav_button(f"peptide:{slug}", p["name"])}
  </div>
</header>

{conflict_block(LIBRARY["entries"]["peptide:" + slug])}
<dl class="peptide-quickfacts">
  <div><dt>Full name</dt><dd>{esc(p["full_name"])}</dd></div>
  <div><dt>Also known as</dt><dd>{esc(aliases)}</dd></div>
  <div><dt>Regulatory status</dt><dd>{esc(p["status"])}</dd></div>
  {f'<div><dt>Variant note</dt><dd>{esc(p["variant_note"])}</dd></div>' if p.get("variant_note") else ''}
</dl>

<div class="ak-sidebar">
  <nav class="ak-toc" aria-label="On this page">
    <p class="ak-eyebrow">On this page</p>
    <ul class="ak-nav">
      {'<li><a href="#biometra">Biometra research</a></li>' if LIBRARY["entries"]["peptide:" + slug]["research"] else ''}
      <li><a href="#origin">Origin</a></li>
      <li><a href="#mechanism">Mechanism</a></li>
      <li><a href="#research">Research summary</a></li>
      <li><a href="#citations">Citations</a></li>
      <li><a href="#benefits">Reported benefits</a></li>
      <li><a href="#dosing">Dosing protocols</a></li>
      <li><a href="#side-effects">Side effects</a></li>
      <li><a href="#safety">Safety notes</a></li>
      <li><a href="#community">Community &amp; reddit notes</a></li>
      <li><a href="#related">Related entries</a></li>
      {'<li><a href="#stacks">Used in stacks</a></li>' if slug in PEPTIDE_STACKS else ''}
      {'<li><a href="#mixing">Mixing compatibility</a></li>' if p.get("mixing_notes") or p.get("mixing_caution") else ''}
    </ul>
  </nav>

  <article class="ak-prose">
    {research_block(LIBRARY["entries"]["peptide:" + slug])}
    <h2>Preserved legacy wiki account</h2>
    <section id="origin" class="ak-section"><h2>Origin</h2><p>{esc(p["origin"])}</p></section>
    <section id="mechanism" class="ak-section"><h2>Mechanism</h2><p>{esc(p["mechanism"])}</p></section>

    <section id="research" class="ak-section">
      <h2>Research summary</h2>
      <div class="ak-exhibit">
        <p class="ak-eyebrow">Evidence</p>
        <p class="ak-takeaway">{esc(p["research_summary"])}</p>
        <p class="ak-source">Legacy status label: {pill(slug)} — not a rating of evidence for every claim. See <a href="/about.html">methodology</a>.</p>
      </div>
    </section>

    <section id="citations" class="ak-section">
      <h2>Citations</h2>
      {citations_block(p.get("citations", []))}
    </section>

    <section id="benefits" class="ak-section"><h2>Reported benefits</h2>{ul(p["reported_benefits"])}</section>

    <section id="dosing" class="ak-section">
      <h2>Dosing protocols reported in the literature &amp; community</h2>
      <p class="ak-small">These are preserved protocols reported by compounding pharmacies, published trials, or self-experimentation communities — not a prescription or recommendation.</p>
      {dosing_table(p["dosing_protocols"])}
    </section>

    <section id="side-effects" class="ak-section"><h2>Side effects</h2>{ul(p["side_effects"])}</section>

    <section id="safety" class="ak-section">
      <h2>Safety notes</h2>
      <div class="ak-banner"><strong>Safety:</strong> {esc(p["safety_notes"])}</div>
    </section>

    <section id="community" class="ak-section">
      <details class="ak-disclosure" open>
        <summary>Community &amp; reddit notes (anecdotal — not clinical evidence)</summary>
        <p>{esc(p["community_notes"])}</p>
      </details>
    </section>

    <section id="related" class="ak-section"><h2>Related entries</h2>{related_list(LIBRARY["entries"]["peptide:" + slug]["related"])}</section>

    {f'<section id="stacks" class="ak-section"><h2>Used in stacks</h2><p class="ak-small">Community combinations that include {esc(p["name"])} — see each stack page for the combination-specific rationale and evidence.</p>{stack_chip_list(PEPTIDE_STACKS.get(slug, []))}</section>' if slug in PEPTIDE_STACKS else ''}

    {f'<section id="mixing" class="ak-section"><h2>Mixing compatibility</h2>{mixing_block(p)}</section>' if p.get("mixing_notes") or p.get("mixing_caution") else ''}
  </article>
</div>
</article>
<script type="application/ld+json">{jsonld}</script>'''
    return page(p["name"], p["tagline"], "", body, canonical=f"/peptides/{slug}.html", page_id=f"peptide-{slug}")

# ---------- category hub pages ----------
def category_page(cslug, c):
    members = CAT_PEPTIDES.get(cslug, [])
    member_set = set(members)
    cat_stacks = [slug for slug, s in STACKS.items() if member_set & set(s["component_slugs"])]
    stacks_block = ""
    if cat_stacks:
        stack_items = "".join(
            f'<li><a href="/stacks/{s}.html">{esc(STACKS[s]["title"])}</a> — <span class="ak-small">{esc(STACKS[s]["tagline"])}</span></li>'
            for s in cat_stacks
        )
        stacks_block = f'''<h2 class="ak-sechead"><span class="ak-n">POPULAR</span> stacks in this category</h2>
<ul>{stack_items}</ul>'''
    cards = "".join(
        f'''<li>
  <a class="card-link" href="/peptides/{s}.html">
    <h3>{esc(PEPTIDES[s]["name"])}</h3>
    <p>{esc(PEPTIDES[s]["tagline"])}</p>
    {pill(s)}
  </a>
</li>''' for s in members
    )
    crumbs = breadcrumbs([("Home", "/index.html"), (c["name"], None)])
    ld = script_json({
        "@context": "https://schema.org", "@type": "CollectionPage", "name": c["name"], "description": c["summary"],
        "hasPart": [{"@type": "MedicalWebPage", "name": PEPTIDES[s]["name"], "url": f"/peptides/{s}.html"} for s in members]
    })
    body = f'''{crumbs}
<header class="ak-pagehead">
  <div>
    <p class="ak-eyebrow">Category</p>
    <h1>{cat_icon(cslug, "cat-icon-lg")} {esc(c["name"])}</h1>
    <p class="ak-lede">{esc(c["summary"])}</p>
  </div>
  <div class="ak-meta">{len(members)} peptides</div>
</header>

<div class="ak-exhibit">
  <p class="ak-eyebrow">Category primer</p>
  <p class="ak-takeaway">{esc(c["primer"])}</p>
</div>

<h2 class="ak-sechead"><span class="ak-n">PEPTIDES</span> in this category</h2>
<ul class="card-grid">{cards}</ul>
{stacks_block}
<script type="application/ld+json">{ld}</script>'''
    return page(c["name"], c["summary"], cslug, body, canonical=f"/categories/{cslug}.html", page_id=f"category-{cslug}")

# ---------- stack pages ----------
EVIDENCE_LEVEL_PILL = {
    "clinical-trial": ("ak-pill-ok", "Combination has clinical trial data"),
    "component-only": ("ak-pill-info", "Components studied separately, not the combination"),
    "speculative": ("ak-pill-warn", "Speculative / community-theorized combination"),
}

def stack_component_cards(slugs):
    cards = "".join(
        f'''<li>
  <a class="card-link" href="/peptides/{s}.html">
    <h3>{esc(PEPTIDES[s]["name"])}</h3>
    <p>{esc(PEPTIDES[s]["tagline"])}</p>
    {pill(s)}
  </a>
</li>''' for s in slugs if s in PEPTIDES
    )
    return f'<ul class="card-grid">{cards}</ul>' if cards else '<p class="ak-small">Component pages not yet listed individually on this wiki.</p>'

def stack_page(slug, s):
    cls, label = EVIDENCE_LEVEL_PILL.get(s["evidence_level"], ("ak-pill-off", "Unclear evidence level"))
    crumbs = breadcrumbs([("Home", "/index.html"), ("Stacks", "/stacks.html"), (s["title"], None)])
    aka = s.get("aka", [])
    aka_line = f'<p class="ak-small">Also known as: {esc(", ".join(aka))}</p>' if aka else ""
    jsonld = script_json({
        "@context": "https://schema.org", "@type": "MedicalWebPage", "name": s["title"],
        "alternateName": aka, "description": s["tagline"],
    })
    body = f'''{crumbs}
<article itemscope itemtype="https://schema.org/MedicalWebPage" data-stack-slug="{esc(slug)}">
<header class="ak-pagehead">
  <div>
    <p class="ak-eyebrow">Peptide stack</p>
    <h1 itemprop="name">{esc(s["title"])}</h1>
    <p class="ak-lede" itemprop="description">{esc(s["tagline"])}</p>
    {aka_line}
    <p class="peptide-pills"><span class="ak-pill {cls}">{esc(label)}</span></p>
  </div>
  <div class="ak-meta">
    <span class="ak-asof">Historical reference · not reverified</span>
    {fav_button(f"stack:{slug}", s["title"])}
  </div>
</header>

<div class="ak-banner"><strong>Not a recommendation.</strong> This page explains why a combination is discussed together in research or community circles — it is not an endorsement of stacking these compounds. See each component's own page for full detail, dosing and safety notes.</div>
{f'<aside class="research-warning"><h2>Unresolved source difference</h2><p>{esc(LIBRARY["stackConflicts"][slug])}</p></aside>' if slug in LIBRARY["stackConflicts"] else ''}

<h2 class="ak-sechead"><span class="ak-n">COMPONENTS</span> in this stack</h2>
{stack_component_cards(s["component_slugs"])}

<article class="ak-prose">
  <section class="ak-section"><h2>Why these are combined</h2><p>{esc(s["rationale"])}</p></section>

  {f'<section class="ak-section"><h2>Mechanism &amp; pharmacokinetics</h2><p>{esc(s["mechanism_pk"])}</p></section>' if s.get("mechanism_pk") else ''}

  <section class="ak-section">
    <h2>Citations</h2>
    {citations_block(s.get("citations", []))}
  </section>

  <section class="ak-section"><h2>Typical community protocol</h2><p>{esc(s["typical_community_protocol"])}</p></section>

  <section class="ak-section">
    <h2>Safety notes</h2>
    <div class="ak-banner"><strong>Safety:</strong> {esc(s["safety_notes"])}</div>
  </section>

  <section class="ak-section">
    <details class="ak-disclosure" open>
      <summary>Community notes (anecdotal — not clinical evidence)</summary>
      <p>{esc(s["community_notes"])}</p>
    </details>
  </section>
</article>
</article>
<script type="application/ld+json">{jsonld}</script>'''
    return page(s["title"], s["tagline"], "stacks", body, canonical=f"/stacks/{slug}.html", page_id=f"stack-{slug}")

def stacks_index_page():
    cards = "".join(
        f'''<li>
  <a class="card-link" href="/stacks/{slug}.html">
    <h3>{esc(s["title"])}</h3>
    {f'<p class="ak-small">AKA {esc(", ".join(s["aka"]))}</p>' if s.get("aka") else ''}
    <p>{esc(s["tagline"])}</p>
    <span class="ak-pill {EVIDENCE_LEVEL_PILL.get(s["evidence_level"], ("ak-pill-off",""))[0]}">{esc(EVIDENCE_LEVEL_PILL.get(s["evidence_level"], ("", "Unclear"))[1])}</span>
  </a>
</li>''' for slug, s in STACKS.items()
    )
    crumbs = breadcrumbs([("Home", "/index.html"), ("Stacks", None)])
    body = f'''{crumbs}
<header class="ak-pagehead">
  <div>
    <p class="ak-eyebrow">Reference</p>
    <h1>Peptide stacks</h1>
    <p class="ak-lede">Combinations of peptides commonly discussed or used together, with the mechanistic rationale, any combination-specific evidence, and links back to each component's own page. These are explanations of community and research practice, not recommendations to combine anything.</p>
  </div>
  <div class="ak-meta">{len(STACKS)} stacks</div>
</header>
<ul class="card-grid">{cards}</ul>'''
    return page("Peptide stacks", "Common peptide combinations, the rationale behind them, and links to each component's page.", "stacks", body, canonical="/stacks.html", page_id="stacks-index")

# ---------- home page ----------
def home_page():
    cat_cards = "".join(
        f'''<li style="--cat-hue:{CATEGORY_HUE.get(c, 200)}" class="cat-card">
  <a class="card-link" href="/categories/{c}.html">
    {cat_icon(c, "cat-icon-lg")}
    <h3>{esc(CATEGORIES[c]["name"])}</h3>
    <p>{esc(CATEGORIES[c]["summary"][:130])}…</p>
    <p class="card-count">{len(CAT_PEPTIDES.get(c, []))} peptides</p>
  </a>
</li>''' for c in CATEGORIES
    )
    kind_links = []
    for kind, label in KIND_LABELS.items():
        count = sum(entry["kind"] == kind for entry in LIBRARY["entries"].values())
        kind_links.append(f'<li><a href="/kinds/{kind}.html">{esc(label)}</a><span>{count} {"entry" if count == 1 else "entries"}</span></li>')
    kind_links = "".join(kind_links)
    ld = script_json({
        "@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "description": SITE_DESC, "url": "/index.html",
        "potentialAction": {"@type": "SearchAction", "target": SITE_DOMAIN + "/directory.html?q={search_term}", "query-input": "required name=search_term"}
    })
    body = f'''<section class="hero">
  <h1>{esc(SITE_NAME)}</h1>
  <p class="ak-lede">{esc(SITE_DESC)}</p>
  <form class="hero-search" role="search" action="/directory.html" method="get">
    <label for="heroSearch" class="visually-hidden">Search the full library</label>
    <input class="ak-input" type="search" id="heroSearch" name="q" placeholder="Search, e.g. BPC-157, caffeine or sleep…" autocomplete="off">
    <button class="ak-btn ak-btn-primary" type="submit">Search</button>
  </form>
</section>

<p class="library-scope"><strong>{len(LIBRARY["entries"])} reference entries</strong> · 210 imported Biometra records · 79 preserved legacy entries · 8 stacks. Overlapping identities are mapped; these counts are not independent studies.</p>
<h2>Explore the library</h2>
<ul class="kind-index">{kind_links}</ul>
<p class="research-status">This is a historical research consolidation, not fresh clinical verification. Study reports, community descriptions and regulatory statements stay distinct. App defaults and rejected drafts are not published here.</p>

<h2 class="ak-sechead">Legacy library by benefit</h2>
<ul class="card-grid">{cat_cards}</ul>

<div class="ak-exhibit">
  <p class="ak-eyebrow">How this wiki is organized</p>
  <p>The <a href="/directory.html">full directory</a> combines the original wiki with all 210 Biometra catalogue records. Exact active-identity matches share their existing page; narrower fragments and premixed products remain distinct when equivalence is uncertain. Each study keeps its population, regimen, duration, outcome and source. Community descriptions and dated negative findings are labelled separately, and conflicting accounts are retained rather than averaged.</p>
  <p class="ak-source">The <a href="/data/library.json">public library JSON</a> retains source associations and occurrence provenance, without app templates or rejected drafts. Original endpoints remain at <a href="/data/peptides.json">peptides.json</a>, <a href="/data/categories.json">categories.json</a> and <a href="/data/stacks.json">stacks.json</a>. See the <a href="/sitemap.xml">sitemap</a> and <a href="/llms.txt">llms.txt</a>.</p>
</div>

<h2 class="ak-sechead"><span class="ak-n">START</span> here</h2>
<ul>
  <li><a href="/dosing-safety.html">Dosing, reconstitution &amp; safety guide</a> — reconstitution math, storage, injection basics, general risk framing.</li>
  <li><a href="/calculator.html">Reconstitution &amp; dose calculator</a> — work out concentration and draw volume for your own vial, with a live 1 mL and 2 mL syringe readout.</li>
  <li><a href="/stacks.html">Peptide stacks</a> — commonly combined peptides, with rationale, evidence level and links back to each component.</li>
  <li><a href="/glossary.html">Glossary</a> — GHRP, GHRH, DAC, half-life and other recurring terms explained once.</li>
  <li><a href="/directory.html">Full directory</a> — every reference entry in one sortable, filterable table.</li>
  <li><a href="/about.html">About &amp; disclaimer</a> — sourcing, limitations, and why this is not medical advice.</li>
</ul>

<div class="ak-exhibit">
  <p class="ak-eyebrow">Open source</p>
  <p>This wiki is free and open source. Browse the code, correct an entry, or add one at <a href="https://github.com/vespassassina/peptide-wiki" rel="noopener">github.com/vespassassina/peptide-wiki</a>.</p>
</div>
<script type="application/ld+json">{ld}</script>'''
    return page(SITE_NAME, SITE_DESC, "home", body, canonical="/index.html", page_id="home")

# ---------- directory page ----------
def directory_page():
    rows = []
    for entry in sorted(LIBRARY["entries"].values(), key=lambda entry: entry["title"].casefold()):
        labels = [TIER_LABELS[research["evidenceTier"]] for research in entry["research"]]
        label = ", ".join(dict.fromkeys(labels)) or "Legacy account"
        search = entry["title"] + " " + " ".join(entry["aliases"]) + " " + json.dumps(entry.get("legacy", {}), ensure_ascii=False)
        search += " " + json.dumps(entry["research"], ensure_ascii=False)
        rows.append(f'''<tr data-kind="{esc(entry["kind"])}" data-search="{esc(search.casefold())}">
<td data-v="{esc(entry["title"])}"><a href="{esc(entry["path"])}">{esc(entry["title"])}</a><br><span class="ak-small">{esc(", ".join(entry["aliases"]))}</span></td>
<td>{esc(KIND_LABELS[entry["kind"]])}</td>
<td>{esc(entry["summary"])}</td>
<td data-v="{esc(label)}">{esc(label)}</td>
</tr>''')
    options = "".join(f'<option value="{kind}">{esc(label)}</option>' for kind, label in KIND_LABELS.items())
    body = f'''{breadcrumbs([("Home", "/index.html"), ("Directory", None)])}
<header class="ak-pagehead">
  <div>
    <p class="ak-eyebrow">Reference</p>
    <h1>Full library directory</h1>
    <p class="ak-lede">Search all {len(LIBRARY["entries"])} entries by name, alias, status or accepted research text. Filter by kind, or sort by name and evidence category.</p>
  </div>
  <div class="ak-meta">{len(LIBRARY["entries"])} entries</div>
</header>
<div class="ak-toolbar dir-controls">
  <label for="dirFilter" class="visually-hidden">Filter directory</label>
  <input class="ak-input" type="search" id="dirFilter" placeholder="Search names, aliases or research…" autocomplete="off">
  <label for="kindFilter" class="visually-hidden">Filter by kind</label>
  <select class="ak-select" id="kindFilter"><option value="">All kinds</option>{options}</select>
</div>
<p class="ak-small">On narrow screens, scroll the table horizontally to read all columns.</p>
<div class="ak-tblwrap" tabindex="0" role="region" aria-label="Scrollable reference directory">
<table class="ak-table" id="directoryTable">
<caption class="ak-vh">Biohacker Wiki reference directory</caption>
<thead><tr>
  <th scope="col" data-sort="s">Entry</th>
  <th scope="col">Kind</th>
  <th scope="col">Summary</th>
  <th scope="col" data-sort="s">Evidence category</th>
</tr></thead>
<tbody>{"".join(rows)}</tbody>
</table>
</div>
<p class="ak-empty" id="noResults" role="status" hidden>No entries match. Clear the search or select another kind.</p><p id="resultCount" role="status" class="ak-small"></p>'''
    extra = '''<script>
(function(){
  ak.table(document.getElementById('directoryTable'), {});
  var input = document.getElementById('dirFilter');
  var kind = document.getElementById('kindFilter');
  var rows = Array.from(document.querySelectorAll('#directoryTable tbody tr'));
  var params = new URLSearchParams(window.location.search);
  input.value = params.get('q') || '';
  if (params.get('kind')) kind.value = params.get('kind');
  function filter(){
    var q = input.value.toLocaleLowerCase().trim(), count = 0;
    rows.forEach(function(row){
      row.hidden = (kind.value && row.dataset.kind !== kind.value) || row.dataset.search.indexOf(q) === -1;
      if (!row.hidden) count++;
    });
    document.getElementById('noResults').hidden = count !== 0;
    document.getElementById('resultCount').textContent = count + ' matching entries';
  }
  input.addEventListener('input', filter); kind.addEventListener('change', filter); filter();
})();
</script>'''
    return page("Full directory", "All reference entries, filterable by name, kind and accepted research.", "directory", body, canonical="/directory.html", page_id="directory", extra_scripts=extra)

# ---------- glossary ----------
GLOSSARY = [
    ("GHRP", "Growth Hormone Releasing Peptide — a class of compounds (e.g. Ipamorelin) that bind the ghrelin receptor to trigger pituitary GH release."),
    ("GHRH", "Growth Hormone Releasing Hormone — the natural hormone (and its analogs, e.g. CJC-1295/Sermorelin) that increases the pituitary's sensitivity and readiness to release GH, typically paired with a GHRP."),
    ("DAC", "Drug Affinity Complex — a chemical modification that binds serum albumin, extending a peptide's half-life from minutes to about a week; used in long-acting CJC-1295 'with DAC', generally viewed as riskier/less controllable than the short-acting version."),
    ("IGF-1", "Insulin-like Growth Factor 1 — the main downstream mediator of growth hormone's tissue-building effects, produced mostly by the liver in response to GH."),
    ("Half-life", "The time it takes for half of an administered dose to be cleared from the body — short half-life compounds need more frequent dosing to maintain effect, but also stop acting faster if something goes wrong."),
    ("Subcutaneous (SubQ)", "Injection into the fatty layer just under the skin, typically the abdomen — the standard route for most self-administered peptides, using an insulin syringe."),
    ("Bacteriostatic water", "Sterile water containing a small amount of benzyl alcohol to inhibit bacterial growth in a multi-use vial; the standard diluent for reconstituting lyophilized (freeze-dried) peptides. Never substitute tap or plain distilled water."),
    ("Reconstitution", "Dissolving a freeze-dried (lyophilized) peptide powder in liquid (usually bacteriostatic water) before it can be measured and injected."),
    ("Units (on an insulin syringe)", "A U-100 insulin syringe has 100 unit markings per 1 mL — 1 unit = 0.01 mL. Peptide dosing math converts a desired microgram dose into a syringe-unit volume based on how much water was used to reconstitute the vial."),
    ("mcg / mg", "Microgram (mcg, 1/1000 of a milligram) and milligram (mg) — most peptide doses are expressed in mcg; mixing these up is a common and dangerous dosing error."),
    ("GLP-1", "Glucagon-Like Peptide-1 — a natural gut hormone that lowers blood sugar and promotes satiety; semaglutide and tirzepatide are synthetic GLP-1 receptor agonists (tirzepatide also activates the GIP receptor)."),
    ("Lyophilized", "Freeze-dried into a stable powder form — how most peptides are shipped and stored before reconstitution."),
    ("Anecdotal / community-reported", "Based on self-reported experiences from online communities rather than controlled clinical trials — useful for hypothesis-generation, not proof of effect."),
    ("Off-label", "Using an approved drug for a purpose other than the one it was specifically approved for — legal for physicians to prescribe, but without the same trial evidence backing that specific use."),
    ("Research chemical", "A compound sold for laboratory research use only, explicitly not for human consumption — the legal fiction under which most self-administered peptides are actually purchased."),
    ("Bioregulator", "A short (usually 2-4 amino acid) synthetic peptide modeled on natural tissue-specific regulatory fragments, developed mostly by Russian researchers (the Khavinson group). Marketed for organ-specific aging support; human trial evidence is thin and largely from the same research lineage."),
    ("Receptor agonist / antagonist", "An agonist binds a receptor and activates it, triggering the cell's normal response (e.g. Ipamorelin agonizes the ghrelin receptor). An antagonist binds the same receptor but blocks it instead of activating it."),
    ("Endogenous / exogenous", "Endogenous means produced naturally by the body (e.g. endogenous GH). Exogenous means introduced from outside it (e.g. an injected peptide). Exogenous administration can suppress the body's own endogenous production through negative feedback."),
    ("PMID / PubMed", "PubMed is the US National Library of Medicine's database of biomedical literature. A PMID (PubMed ID) is the unique number identifying an indexed paper — the citation links on this site point to pubmed.ncbi.nlm.nih.gov/{PMID}."),
    ("RCT (randomized controlled trial)", "A study where participants are randomly assigned to receive the treatment or a control/placebo, reducing bias — the strongest common evidence type for whether a treatment actually works in humans. Most peptides on this site have no RCT evidence at all."),
    ("In vitro / in vivo", "In vitro: in a lab dish or test tube, outside a living organism (cell cultures). In vivo: inside a living organism (animal or human). In vitro findings frequently fail to replicate in vivo — treat them as a first hint, not a result."),
    ("Meta-analysis / systematic review", "A meta-analysis statistically pools results from multiple studies to estimate an overall effect; a systematic review summarizes them without necessarily pooling the numbers. Both sit above individual trials in evidence strength, when enough trials exist to review — which is rare for research peptides."),
    ("Bioavailability", "The fraction of an administered dose that actually reaches systemic circulation intact. Most peptides have poor oral bioavailability (stomach acid and enzymes break them down), which is why almost all of them are injected rather than swallowed."),
    ("First-pass metabolism", "The breakdown of a substance by the liver and gut wall before it reaches general circulation, after oral absorption. A major reason peptides are dosed by injection instead of pill."),
    ("Titration", "Gradually increasing (or decreasing) a dose over time to find the level that works with tolerable side effects, rather than jumping straight to a target dose — standard practice for GLP-1 drugs and GH secretagogues."),
    ("TFA / acetate salt form", "The counter-ion a peptide is synthesized and sold with. Acetate is generally preferred for injectables; TFA (trifluoroacetate), common in cheaper research-grade synthesis, is more cytotoxic in cell studies and considered lower quality for anything injected."),
    ("Purity / HPLC testing", "HPLC (high-performance liquid chromatography) separates and quantifies the actual peptide content of a vial versus contaminants or degraded product. A certificate of analysis (CoA) showing HPLC purity is the main way to check whether a research-chemical source is selling what it claims."),
    ("Half-life extension (PEGylation, DAC, Fc-fusion)", "Chemical modification techniques that slow a peptide's clearance from the body, cutting dosing frequency. Comes with trade-offs: less precise control over blood levels and, in some cases, altered receptor binding versus the native peptide."),
    ("Ghrelin receptor (GHS-R)", "The growth-hormone-secretagogue receptor. Ghrelin is its natural ligand; GHRPs and compounds like Ipamorelin and MK-677 are synthetic agonists that trigger pituitary GH release through this same receptor."),
    ("Melanocortin receptor (MC1R-MC5R)", "A family of five receptors involved in pigmentation, appetite, inflammation, and sexual arousal depending on subtype. PT-141 and MT-1/MT-2 work through this receptor family — different subtype selectivity explains their different effect profiles."),
]

def glossary_page():
    items = "".join(f'<div class="glossary-item"><dt id="{esc(term.lower().replace(" ","-").replace("(","").replace(")","").replace("/","-"))}">{esc(term)}</dt><dd>{esc(defn)}</dd></div>' for term, defn in GLOSSARY)
    body = f'''{breadcrumbs([("Home", "/index.html"), ("Glossary", None)])}
<header class="ak-pagehead"><div><p class="ak-eyebrow">Reference</p><h1>Glossary</h1><p class="ak-lede">Recurring terms explained once so leaf pages can stay focused on the peptide itself.</p></div></header>
<div class="glossary-list"><dl>{items}</dl></div>'''
    return page("Glossary", "Definitions of recurring peptide-world terms: GHRP, GHRH, DAC, half-life, reconstitution and more.", "glossary", body, canonical="/glossary.html", page_id="glossary")

# ---------- dosing & safety ----------
def dosing_safety_page():
    body = f'''{breadcrumbs([("Home", "/index.html"), ("Dosing & safety", None)])}
<header class="ak-pagehead"><div><p class="ak-eyebrow">Reference</p><h1>Dosing, reconstitution &amp; safety guide</h1><p class="ak-lede">General mechanics that apply across most injectable peptides. Peptide-specific protocols live on each <a href="/directory.html">peptide's own page</a>; this page covers the shared basics.</p></div></header>

<article class="ak-prose">
<section class="ak-section"><h2>Supplies for subcutaneous injection</h2>
<ul>
<li><strong>Insulin syringes with needles</strong> — 29–30 gauge, 1 mL (100-unit) barrel, roughly ½ inch needle length is a common combination.</li>
<li><strong>Alcohol wipes</strong> — sanitize vial seals and injection-site skin before every injection.</li>
<li><strong>Bacteriostatic water</strong> — the standard diluent for reconstituting freeze-dried peptide powder. Never use tap water or plain store-bought distilled water, which lack the antimicrobial preservative and are not sterile for injection.</li>
</ul>
</section>

<section class="ak-section"><h2>Reconstitution math, worked example</h2>
<p>Goal: dissolve a known weight of peptide (e.g. 5 mg) in a volume of bacteriostatic water (e.g. 2 mL), then draw the correct syringe-unit volume to deliver your intended dose.</p>
<p><strong>Conversions:</strong> 100 units = 1 mL · 1 unit = 0.01 mL · 1 mg = 1,000 mcg</p>
<p><strong>Worked example:</strong> a 5 mg vial, reconstituted with 2 mL of bacteriostatic water, gives a concentration of 2,500 mcg/mL, i.e. 25 mcg per syringe unit. To deliver a 250 mcg dose, draw 10 units.</p>
<div class="ak-tblwrap"><table class="ak-table">
<caption class="ak-vh">Example dosing chart, 5 mg in 2 mL</caption>
<thead><tr><th scope="col">Units drawn</th><th scope="col">Dose delivered (5 mg / 2 mL)</th></tr></thead>
<tbody>
<tr><td>2</td><td>50 mcg</td></tr>
<tr><td>4</td><td>100 mcg</td></tr>
<tr><td>6</td><td>150 mcg</td></tr>
<tr><td>8</td><td>200 mcg</td></tr>
<tr><td>10</td><td>250 mcg</td></tr>
</tbody></table></div>
<p class="ak-small">For a blend of two peptides in one vial (e.g. Ipamorelin + Mod-GRF), calculate reconstitution volume based on one peptide's target dose — the other is delivered at the same proportional dose per unit, since both were weighed in equally.</p>
</section>

<section class="ak-section"><h2>Storage</h2>
<ul>
<li>Keep lyophilized (powder) peptides in the freezer until ready to reconstitute.</li>
<li>Reconstitute only what you plan to use over the following weeks — not the entire stock at once.</li>
<li>Keep reconstituted peptides refrigerated (not frozen) and shielded from light; most tolerate a few weeks refrigerated, though stability varies by compound.</li>
<li>Avoid repeated freeze-thaw cycles of reconstituted (liquid) peptide.</li>
<li>Swab vial seals with alcohol before every draw to reduce contamination risk across a multi-use vial.</li>
</ul>
</section>

<section class="ak-section"><h2>General safety framing</h2>
<div class="ak-banner"><strong>Start low.</strong> Individual sensitivity varies substantially, and allergic-type reactions are reported anecdotally even to compounds generally considered gentle (e.g. GH secretagogues). Start at the low end of any reported dose range and monitor for flushing, itching, hives, or heart palpitations, which are treated in the community as signals to stop, not to push through.</div>
<ul>
<li><strong>Sourcing matters.</strong> Most peptides discussed in this wiki are sold as research chemicals, "not for human consumption," outside any regulatory quality-control framework. Purity, dosing accuracy and even correct identity of the compound in the vial are not guaranteed.</li>
<li><strong>Evidence quality varies enormously peptide-to-peptide.</strong> Some compounds in this wiki (semaglutide, tirzepatide, tesamorelin, Thymosin Alpha-1) are FDA-approved drugs or have gone through real placebo-controlled human trials. Others (MOTS-c, Humanin, IGF-1 LR3) have essentially no human trial data at all. Check each peptide's own status pill and research-summary section.</li>
<li><strong>Talk to a physician</strong>, ideally one familiar with peptide therapy, especially before combining multiple compounds, if you have any chronic condition, are on other medications, or have a personal/family history of cancer.</li>
</ul>
</section>
</article>'''
    return page("Dosing & safety guide", "Reconstitution math, storage, injection supplies and general safety framing shared across most injectable peptides.", "dosing-safety", body, canonical="/dosing-safety.html", page_id="dosing-safety")

# ---------- calculator ----------
def syringe_block(prefix, title, note):
    return f'''<div class="pw-syringe">
    <p class="ak-eyebrow">{esc(title)}</p>
    <svg viewBox="-120 0 1000 170" class="pw-syringe-svg" role="img" aria-labelledby="{prefix}-svgtitle">
      <title id="{prefix}-svgtitle">{esc(title)}, plunger position shows the calculated draw</title>
      <line x1="820" y1="80" x2="866" y2="80" stroke="var(--ak-ink-soft)" stroke-width="3"/>
      <polygon points="866,73 884,80 866,87" fill="var(--ak-ink-soft)"/>
      <rect id="{prefix}-fill" x="820" y="57" width="0" height="46" fill="var(--ak-accent)" opacity="0.5"/>
      <rect x="400" y="55" width="420" height="50" rx="6" fill="none" stroke="var(--ak-ink)" stroke-width="2"/>
      <g id="{prefix}-ticks" font-size="12" fill="var(--ak-ink-soft)"></g>
      <rect id="{prefix}-stopper" x="815" y="53" width="10" height="54" fill="var(--ak-ink-soft)" rx="1.5"/>
      <g id="{prefix}-plunger">
        <rect x="330" y="72" width="70" height="16" fill="var(--ak-ink-soft)"/>
        <rect x="300" y="55" width="10" height="50" fill="var(--ak-ink-soft)"/>
        <rect x="264" y="48" width="38" height="64" rx="3" fill="var(--ak-ink-soft)"/>
      </g>
    </svg>
    <p class="pw-syringe-readout" id="{prefix}-readout">Enter values above</p>
    <p class="ak-small">{esc(note)}</p>
  </div>'''

def calculator_page():
    body = f'''{breadcrumbs([("Home", "/index.html"), ("Calculator", None)])}
<header class="ak-pagehead">
  <div>
    <p class="ak-eyebrow">Tool</p>
    <h1>Reconstitution &amp; dose calculator</h1>
    <p class="ak-lede">Works out concentration from a vial's peptide content and the bacteriostatic water added, then shows the syringe draw for a target dose — with a live 1&nbsp;mL (100-unit insulin) and 2&nbsp;mL syringe readout. All calculation happens in your browser; nothing here is sent anywhere.</p>
  </div>
</header>

<div class="ak-banner ak-banner-bad"><strong>Not medical advice.</strong> This tool does arithmetic on the numbers you enter — it has no way to verify your vial's actual labelled content, your syringe's actual markings, or whether a given dose is appropriate for you. Always read your vial and syringe against what you enter here before drawing anything, and see the <a href="/dosing-safety.html">dosing &amp; safety guide</a>.</div>

<article class="ak-prose">
<section class="ak-section" id="reconstitution">
  <h2>1. Reconstitution</h2>
  <div class="calc-grid">
    <div class="calc-field">
      <label for="calcMg">Peptide in vial</label>
      <div class="calc-inline"><input class="ak-input" type="number" id="calcMg" min="0" step="0.01" value="5"> <span class="ak-small">mg</span></div>
    </div>
    <div class="calc-field">
      <label for="calcWater">Bacteriostatic water added</label>
      <div class="calc-inline"><input class="ak-input" type="number" id="calcWater" min="0.01" step="0.01" value="2"> <span class="ak-small">mL</span></div>
      <div class="calc-presets" role="group" aria-label="Common water volumes">
        <button type="button" class="ak-btn calc-preset" data-water="1">1 mL</button>
        <button type="button" class="ak-btn calc-preset" data-water="2">2 mL</button>
        <button type="button" class="ak-btn calc-preset" data-water="3">3 mL</button>
        <button type="button" class="ak-btn calc-preset" data-water="5">5 mL</button>
      </div>
    </div>
  </div>
  <div class="ak-exhibit" id="calcConcOut">
    <p class="ak-eyebrow">Resulting concentration</p>
    <p class="ak-takeaway" id="calcConcText">—</p>
  </div>
</section>

<section class="ak-section" id="dose">
  <h2>2. Target dose</h2>
  <div class="calc-grid">
    <div class="calc-field">
      <label for="calcDose">Desired dose</label>
      <div class="calc-inline">
        <input class="ak-input" type="number" id="calcDose" min="0" step="1" value="250">
        <select class="ak-select" id="calcDoseUnit">
          <option value="mcg" selected>mcg</option>
          <option value="mg">mg</option>
        </select>
      </div>
    </div>
  </div>
  <div class="ak-exhibit" id="calcDoseOut">
    <p class="ak-eyebrow">Draw</p>
    <p class="ak-takeaway" id="calcDoseText">—</p>
  </div>
  <p class="ak-small" id="calcOverflowNote" hidden></p>
</section>

<section class="ak-section" id="syringes">
  <h2>3. Where to pull the plunger</h2>
  <div class="pw-syringe-grid">
    {syringe_block("s1", "1 mL insulin syringe (100 units)", "Standard insulin syringe, marked in units. 100 units = 1 mL = 20 units per 0.2 mL major line.")}
    {syringe_block("s2", "2 mL syringe", "Standard Luer syringe marked in 0.1 mL graduations, no unit markings.")}
  </div>
  <p class="ak-small">If a reading exceeds a syringe's barrel, the fill shows full red rather than overflowing — switch to the larger syringe, or reconstitute with more water to bring the draw volume back within range.</p>
</section>
</article>'''
    extra = '''<script>
(function(){
  var BARREL_LEFT = 400, BARREL_RIGHT = 820, BARREL_LEN = BARREL_RIGHT - BARREL_LEFT;

  function fmt(n, d){
    if (!isFinite(n)) return "0";
    var f = n.toFixed(d);
    return f.replace(/\\.0+$/,'').replace(/(\\.\\d*?)0+$/,'$1').replace(/\\.$/,'');
  }

  function drawTicks(prefix, capacity, step, labelStep, labelFmt){
    var g = document.getElementById(prefix + '-ticks');
    if (!g) return;
    g.innerHTML = '';
    var n = Math.round(capacity / step);
    for (var i = 0; i <= n; i++){
      var v = i * step;
      var x = BARREL_RIGHT - (v / capacity) * BARREL_LEN;
      var isMajor = Math.round(v / labelStep) * labelStep === Math.round(v * 1000) / 1000;
      var tickTop = isMajor ? 55 : 62;
      var line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', x); line.setAttribute('x2', x);
      line.setAttribute('y1', tickTop); line.setAttribute('y2', 105);
      line.setAttribute('stroke', 'var(--ak-ink-soft)');
      line.setAttribute('stroke-width', isMajor ? '1.5' : '1');
      g.appendChild(line);
      if (isMajor){
        var text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', x); text.setAttribute('y', 120);
        text.setAttribute('text-anchor', 'middle');
        text.textContent = labelFmt(v);
        g.appendChild(text);
      }
    }
  }

  function setSyringe(prefix, fraction){
    var overflow = fraction > 1;
    var f = Math.max(0, Math.min(1, fraction));
    var stopperX = BARREL_RIGHT - f * BARREL_LEN;
    var fill = document.getElementById(prefix + '-fill');
    var stopper = document.getElementById(prefix + '-stopper');
    var plunger = document.getElementById(prefix + '-plunger');
    if (fill){
      fill.setAttribute('x', stopperX);
      fill.setAttribute('width', Math.max(0, BARREL_RIGHT - stopperX));
      fill.setAttribute('fill', overflow ? 'var(--ak-neg)' : 'var(--ak-accent)');
      fill.setAttribute('opacity', overflow ? '0.6' : '0.5');
    }
    if (stopper) stopper.setAttribute('x', stopperX - 5);
    if (plunger) plunger.setAttribute('transform', 'translate(' + (stopperX - BARREL_RIGHT) + ',0)');
  }

  drawTicks('s1', 100, 10, 20, function(v){ return fmt(v, 0); });
  drawTicks('s2', 2, 0.2, 0.4, function(v){ return fmt(v, 1); });
  setSyringe('s1', 0); setSyringe('s2', 0);

  var mgEl = document.getElementById('calcMg');
  var waterEl = document.getElementById('calcWater');
  var doseEl = document.getElementById('calcDose');
  var doseUnitEl = document.getElementById('calcDoseUnit');
  var concText = document.getElementById('calcConcText');
  var doseText = document.getElementById('calcDoseText');
  var overflowNote = document.getElementById('calcOverflowNote');
  var readout1 = document.getElementById('s1-readout');
  var readout2 = document.getElementById('s2-readout');

  function recalc(){
    var mg = parseFloat(mgEl.value) || 0;
    var water = parseFloat(waterEl.value) || 0;
    var doseRaw = parseFloat(doseEl.value) || 0;
    var doseMcg = doseUnitEl.value === 'mg' ? doseRaw * 1000 : doseRaw;

    if (mg <= 0 || water <= 0){
      concText.textContent = 'Enter a vial amount and water volume above.';
      doseText.textContent = '—';
      readout1.textContent = 'Enter values above';
      readout2.textContent = 'Enter values above';
      setSyringe('s1', 0); setSyringe('s2', 0);
      overflowNote.hidden = true;
      return;
    }

    var concMcgPerMl = (mg * 1000) / water;
    var mcgPerUnit = concMcgPerMl / 100;
    concText.textContent = fmt(concMcgPerMl, 1) + ' mcg/mL — ' + fmt(mcgPerUnit, 2) + ' mcg per unit on a 1 mL (100-unit) syringe.';

    if (doseMcg <= 0){
      doseText.textContent = 'Enter a target dose above.';
      readout1.textContent = 'Enter a target dose above';
      readout2.textContent = 'Enter a target dose above';
      setSyringe('s1', 0); setSyringe('s2', 0);
      overflowNote.hidden = true;
      return;
    }

    var volumeMl = doseMcg / concMcgPerMl;
    var units = volumeMl * 100;
    doseText.textContent = 'Draw ' + fmt(volumeMl, 3) + ' mL (' + fmt(units, 1) + ' units) to deliver ' + fmt(doseMcg, 1) + ' mcg.';

    var f1 = units / 100;
    var f2 = volumeMl / 2;
    setSyringe('s1', f1);
    setSyringe('s2', f2);
    readout1.textContent = f1 > 1 ? 'Exceeds 1 mL barrel — use the 2 mL syringe or add more water' : 'Pull to ' + fmt(units, 1) + ' units (' + fmt(volumeMl, 2) + ' mL)';
    readout2.textContent = f2 > 1 ? 'Exceeds 2 mL barrel — reconstitute with more water' : 'Pull to ' + fmt(volumeMl, 2) + ' mL';

    if (f1 > 1 || f2 > 1){
      overflowNote.hidden = false;
      overflowNote.textContent = 'This draw volume exceeds at least one syringe shown. Add more bacteriostatic water to lower the concentration, or use a larger syringe.';
    } else {
      overflowNote.hidden = true;
    }
  }

  [mgEl, waterEl, doseEl].forEach(function(el){ el.addEventListener('input', recalc); });
  doseUnitEl.addEventListener('change', recalc);
  document.querySelectorAll('.calc-preset').forEach(function(btn){
    btn.addEventListener('click', function(){
      waterEl.value = btn.getAttribute('data-water');
      recalc();
    });
  });
  recalc();
})();
</script>'''
    return page("Reconstitution & dose calculator", "Calculate peptide reconstitution concentration and syringe draw volume, with a live 1 mL and 2 mL syringe visual.", "calculator", body, canonical="/calculator.html", page_id="calculator", extra_scripts=extra)

# ---------- about ----------
def about_page():
    body = f'''{breadcrumbs([("Home", "/index.html"), ("About", None)])}
<header class="ak-pagehead"><div><p class="ak-eyebrow">Reference</p><h1>About &amp; disclaimer</h1></div></header>
<article class="ak-prose">
<section class="ak-section"><h2>What this is</h2>
<p>Biohacker Wiki combines this preserved legacy account with all 210 authored Biometra catalogue records across eight kinds. The repository and Pages URL remain unchanged. Exact active-identity matches retain old routes; narrower fragments and premixed products stay distinct where equivalence is uncertain.</p>
<p>Imported research is a historical snapshot, not newly verified clinical guidance. B-82 checks dated 2026-10-06 retain their original scope: 59 suitable descriptions and 71 bounded empty outcomes. Source-to-wiki backlinks are circular provenance, not independent corroboration. App defaults and rejected drafts remain in the non-deployed archive. Fresh suitability/rights review and separate owner approval are required before new public republication; neither is claimed by this local build.</p>
<p>The full library covers peptides, medications and hormones, supplements, food and fasting, exercise, recovery practices, context and habits, and lab markers. The original peptide benefit categories remain available. Published study reports, regulatory statements and community accounts stay attributable and separate.</p>
</section>
<section class="ak-section"><h2>This is not medical advice</h2>
<div class="ak-banner ak-banner-bad">Nothing on this site is a recommendation to use, or a guide to using, any specific substance. Many peptides described here are unapproved research chemicals sold "not for human consumption," with limited to no human safety or efficacy data at the doses commonly self-administered. Always consult a licensed physician before starting, stopping, or combining any of these substances.</div>
</section>
<section class="ak-section"><h2>Evidence categories and regulatory status</h2>
<p>Imported source categories are regulator/guideline, systematic review, clinical study, preclinical, or reference only. These describe a source category, not a numerical ranking, current approval, human efficacy or safety. Read each study's population, route and limitations. Missing study protocols, absent community records and dated researched-empty findings are different states.</p>
<h3>Legacy regulatory/status labels</h3>
<p>The following editorial labels remain on legacy peptide pages and benefit categories. They are not fresh regulatory checks or evidence ratings. Approval for one indication does not establish suitability for another:</p>
<p>
<span class="ak-pill ak-pill-ok">Approved drug</span> — genuine FDA (or comparable) drug approval, backed by real trials, for at least one indication.<br>
<span class="ak-pill ak-pill-info">Approved abroad / formerly approved</span> — real drug approval exists, but not from the FDA, or the branded product was later discontinued for commercial reasons.<br>
<span class="ak-pill ak-pill-warn">Investigational</span> — actively in human clinical trials, not yet approved.<br>
<span class="ak-pill ak-pill-off">Research chemical</span> — sold "not for human consumption," no meaningful human trial data.<br>
<span class="ak-pill ak-pill-risk">Elevated caution</span> — either failed its own efficacy trial, or carries a specific, documented safety signal worth extra attention.
</p>
<p class="ak-small">One category deserves a separate note: <a href="/categories/bioregulators.html">Peptide bioregulators</a> collects the Khavinson/St. Petersburg Institute organ-targeted peptide tradition. Nearly all of that category's evidence comes from a small number of Russian-language, Russian-institution studies with limited independent replication — a narrower evidence base than the rest of this wiki, even where a compound also carries formal Russian drug approval. Read that category's primer before treating any status pill in it as comparable to an FDA-approved-drug pill elsewhere on the site.</p>
</section>
<section class="ak-section"><h2>Sourcing &amp; methodology</h2>
<p>Content draws on: peer-reviewed research summaries and trial data where publicly described in the literature (including regulatory trial program names like STEP, SURMOUNT and SELECT for the GLP-1-class drugs, and RegeneRx's published Thymosin Beta-4 development program); regulatory/drug-approval status by country; compounding-pharmacy dosing guides; and long-running self-experimentation community documentation, most notably the u/BoldMeasures <em>Peptide Primer</em> reddit archive, which provided detailed grounding for BPC-157, TB-500/Thymosin Beta-4, Ipamorelin, Mod-GRF (CJC-1295 without DAC) and ARA-290, including specific reconstitution and dosing methodology reused across the <a href="/dosing-safety.html">dosing &amp; safety guide</a>. Community-sourced sections are explicitly labelled as anecdotal on every leaf page and should be weighted accordingly.</p>
<p class="ak-small">This wiki does not sell anything and has no vendor affiliations. It is built with <a href="https://github.com/vespassassina/artifactkit">artifactkit</a>, an open-source component kit for AI-generated HTML.</p>
</section>
<section class="ak-section"><h2>Limitations</h2>
<ul>
<li>Research summaries are condensed for readability and are not a substitute for reading primary sources.</li>
<li>The peptide/research-chemical landscape changes quickly; treat regulatory-status statements as a snapshot as of the last update rather than guaranteed current.</li>
<li>Community/anecdotal sections reflect commonly reported patterns in online self-experimentation communities, which are not representative samples and are subject to selection and confirmation bias.</li>
</ul>
</section>
</article>'''
    return page("About & disclaimer", "Methodology, historical provenance and the disclaimer governing Biohacker Wiki.", "about", body, canonical="/about.html", page_id="about")

# ---------- favorites (client-side, cookie-backed) ----------
def favorites_page():
    favorite_index = [
        {"id": entry["id"], "title": entry["title"], "summary": entry["summary"],
         "path": entry["path"], "kind": KIND_LABELS[entry["kind"]]}
        for entry in sorted(LIBRARY["entries"].values(), key=lambda entry: entry["title"].casefold())
    ] + [
        {"id": "stack:" + slug, "title": stack["title"], "summary": stack["tagline"],
         "path": f"/stacks/{slug}.html", "kind": "Stack"}
        for slug, stack in STACKS.items()
    ]
    body = f'''{breadcrumbs([("Home", "/index.html"), ("Favorites", None)])}
<header class="ak-pagehead">
  <div>
    <p class="ak-eyebrow">Your list</p>
    <h1>★ Favorites</h1>
    <p class="ak-lede">Reference entries and stacks you've starred, kept in this browser. Existing peptide and stack selections are retained. Clearing cookies or switching browsers clears this list.</p>
  </div>
</header>
<div id="favoritesRoot">
  <p class="ak-small">Loading…</p>
</div>
<script type="application/json" id="pwFavoriteIndex">{script_json(favorite_index)}</script>'''
    return page("Favorites", "Reference entries and stacks you've starred, saved in this browser.", "favorites", body, canonical="/favorites.html", page_id="favorites")

def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if path.endswith(".html"):
        content = relativize_links(path, content)
    with open(full, "w") as f:
        f.write(content)

SITE_JS = """
(function(){
  var toggle = document.getElementById('navToggle');
  var nav = document.getElementById('siteNav');
  if (toggle && nav) {
    toggle.addEventListener('click', function(){
      var open = nav.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }
})();

/* ---- favorites: plain array of "peptide:slug" / "stack:slug" keys, stored
   in a first-party cookie (no server, nothing sent anywhere). ---- */
window.ak = window.ak || {};
(function(){
  var COOKIE = 'pw_favorites';
  var siteRoot = new URL('../', document.currentScript.src);
  var MAX_AGE = 60 * 60 * 24 * 400; // ~400 days, the practical cap most browsers allow

  function report(message){
    var notice = document.getElementById('favoriteError');
    if (!notice) {
      notice = document.createElement('p'); notice.id = 'favoriteError';
      notice.className = 'research-warning'; notice.setAttribute('role', 'alert');
      document.getElementById('main').prepend(notice);
    }
    notice.textContent = message;
  }

  function readFavorites(){
    try {
      var match = document.cookie.split('; ').find(function(row){ return row.indexOf(COOKIE + '=') === 0; });
      if (!match) return [];
      var raw = decodeURIComponent(match.split('=').slice(1).join('='));
      var parsed = JSON.parse(raw);
      if (!Array.isArray(parsed) || !parsed.every(function(k){ return typeof k === 'string'; })) {
        report('Saved favorites have an invalid format. No selections were changed. Clear this site’s favorites cookie to reset it.');
        return null;
      }
      return parsed;
    } catch (e) {
      report('Saved favorites could not be read. No selections were changed. Check browser cookie settings or clear this site’s favorites cookie.');
      return null;
    }
  }

  function writeFavorites(list){
    document.cookie = COOKIE + '=' + encodeURIComponent(JSON.stringify(list)) + '; path=/; max-age=' + MAX_AGE + '; samesite=lax';
    var saved = readFavorites();
    if (!saved || JSON.stringify(saved) !== JSON.stringify(list)) throw new Error('Cookie was not saved');
  }

  function isFav(key){ var list = readFavorites(); return list !== null && list.indexOf(key) !== -1; }

  function toggleFav(key){
    var list = readFavorites();
    if (list === null) return null;
    var i = list.indexOf(key);
    if (i === -1) { list.push(key); } else { list.splice(i, 1); }
    try { writeFavorites(list); }
    catch (e) { report('Favorites could not be saved. Enable cookies for this site and retry; the change was not confirmed.'); return null; }
    return list.indexOf(key) !== -1;
  }

  function setButtonState(btn, on){
    btn.setAttribute('aria-pressed', on ? 'true' : 'false');
    btn.classList.toggle('is-fav', on);
    var star = btn.querySelector('.fav-star');
    var label = btn.querySelector('.fav-label');
    if (star) star.textContent = on ? '★' : '☆';
    if (label) label.textContent = on ? 'Favorited' : 'Add to favorites';
  }

  document.addEventListener('DOMContentLoaded', function(){
    var buttons = document.querySelectorAll('.fav-toggle[data-fav-key]');
    buttons.forEach(function(btn){
      var key = btn.getAttribute('data-fav-key');
      setButtonState(btn, isFav(key));
      btn.addEventListener('click', function(){
        var state = toggleFav(key);
        if (state !== null) setButtonState(btn, state);
      });
    });
  });

  ak.renderFavorites = function(){
    var root = document.getElementById('favoritesRoot');
    if (!root) return;
    var index = JSON.parse(document.getElementById('pwFavoriteIndex').textContent);
    var favs = readFavorites();
    if (favs === null) { root.textContent = 'Favorites unavailable. See the error above.'; return; }
    var items = index.filter(function(item){ return favs.indexOf(item.id) !== -1; });
    root.replaceChildren();
    if (!items.length) {
      root.textContent = favs.length ? 'No saved keys match this catalogue. Your keys were retained in the cookie.' : 'No favorites yet. Open any entry or stack and select Add to favorites.';
      return;
    }
    var list = document.createElement('ul'); list.className = 'research-index';
    items.forEach(function(item){
      var li = document.createElement('li'), a = document.createElement('a'), p = document.createElement('p');
      a.href = new URL(item.path.replace(/^\\//, ''), siteRoot).href;
      a.textContent = item.title; p.textContent = item.kind + ' — ' + item.summary;
      li.append(a, p); list.append(li);
    });
    root.append(list);
    var unknown = favs.filter(function(key){ return !index.some(function(item){ return item.id === key; }); });
    if (unknown.length) {
      var note = document.createElement('p');
      note.textContent = unknown.length + ' saved keys are not in this catalogue; they were retained in your cookie.';
      root.append(note);
    }
  };

  document.addEventListener('DOMContentLoaded', function(){ ak.renderFavorites(); });
})();
"""

def build():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)

    write("index.html", home_page())
    write("directory.html", directory_page())
    write("glossary.html", glossary_page())
    write("dosing-safety.html", dosing_safety_page())
    write("calculator.html", calculator_page())
    write("about.html", about_page())
    write("favorites.html", favorites_page())
    for cslug, c in CATEGORIES.items():
        write(f"categories/{cslug}.html", category_page(cslug, c))
    for slug, p in PEPTIDES.items():
        write(f"peptides/{slug}.html", peptide_page(slug, p))
    write("stacks.html", stacks_index_page())
    for slug, s in STACKS.items():
        write(f"stacks/{slug}.html", stack_page(slug, s))
    for entry in LIBRARY["entries"].values():
        if entry["id"].startswith("library:"):
            write(entry["path"].lstrip("/"), library_page(entry))
    for kind in KIND_LABELS:
        write(f"kinds/{kind}.html", kind_page(kind))

    # vendor artifactkit assets + our site chrome
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    for fname in ["theme.css", "components.css", "print.css", "core.js", "site.css"]:
        shutil.copy(os.path.join(VENDOR, fname), os.path.join(OUT, "assets", fname))
    write("assets/site.js", SITE_JS)

    # machine-readable data
    write("data/peptides.json", json.dumps(PEPTIDES, indent=2))
    write("data/categories.json", json.dumps(CATEGORIES, indent=2))
    write("data/stacks.json", json.dumps(STACKS, indent=2))
    write("data/library.json", json.dumps(LIBRARY, indent=2, ensure_ascii=False))
    sitemap_urls = ["/index.html", "/directory.html", "/glossary.html", "/dosing-safety.html", "/about.html", "/stacks.html", "/favorites.html", "/calculator.html"]
    sitemap_urls += [f"/categories/{c}.html" for c in CATEGORIES]
    sitemap_urls += [f"/peptides/{s}.html" for s in ALL_SLUGS]
    sitemap_urls += [f"/stacks/{s}.html" for s in ALL_STACK_SLUGS]
    sitemap_urls += [entry["path"] for entry in LIBRARY["entries"].values() if entry["id"].startswith("library:")]
    sitemap_urls += [f"/kinds/{kind}.html" for kind in KIND_LABELS]
    write("data/sitemap.json", json.dumps({"site": SITE_NAME, "generated": TODAY, "pages": sitemap_urls, "categories": {c: CAT_PEPTIDES.get(c, []) for c in CATEGORIES}}, indent=2))

    xml_urls = "".join(f"<url><loc>{SITE_DOMAIN}{u}</loc></url>" for u in sitemap_urls)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{xml_urls}</urlset>')

    lines = [f"# {SITE_NAME}", "", SITE_DESC, "", "Historical snapshot; not freshly verified. Fresh suitability/rights review required before republication.", "", "## Full library (data/library.json)"]
    for entry in sorted(LIBRARY["entries"].values(), key=lambda entry: entry["title"].casefold()):
        lines.append(f'- {entry["title"]} ({SITE_DOMAIN}{entry["path"]}) — {entry["summary"]}')
    lines += ["", "## Kinds"]
    for kind, label in KIND_LABELS.items():
        lines.append(f"- {label} ({SITE_DOMAIN}/kinds/{kind}.html)")
    lines += ["", "## Legacy benefit categories"]
    for c, cc in CATEGORIES.items():
        lines.append(f"- {cc['name']} (/categories/{c}.html): {cc['summary']}")
    lines += ["", "## Peptides (machine-readable data at /data/peptides.json)"]
    for s in ALL_SLUGS:
        p = PEPTIDES[s]
        lines.append(f"- {p['name']} (/peptides/{s}.html) — {p['tagline']} [{tier(s)[1]}]")
    lines += ["", "## Stacks (combinations, /stacks.html)"]
    for s in ALL_STACK_SLUGS:
        lines.append(f"- {STACKS[s]['title']} (/stacks/{s}.html) — {STACKS[s]['tagline']}")
    lines += ["", "## Notes for agents", "Every page has JSON-LD structured data (MedicalWebPage/CollectionPage + BreadcrumbList).", "Flat JSON dataset: /data/peptides.json, /data/categories.json, /data/stacks.json, /data/sitemap.json", "This is not medical advice — see /about.html."]
    write("llms.txt", "\n".join(lines))

    print(f"Generated {len(LIBRARY['entries'])} reference entries, {len(STACKS)} stacks and {len(CATEGORIES)} legacy categories")

def main():
    global LIBRARY, OUT
    LIBRARY = load_library(Path(SRC))
    destination = Path(OUT)
    if destination.is_symlink():
        raise ValueError("Build output is a symlink; choose a normal output directory. Nothing was replaced.")
    destination = destination.absolute()
    original_out = OUT
    with tempfile.TemporaryDirectory(prefix=".wiki-build-", dir=destination.parent) as directory:
        stage, backup = Path(directory) / "site", Path(directory) / "previous"
        try:
            OUT = str(stage)
            build()
            if destination.exists():
                destination.rename(backup)
            try:
                stage.rename(destination)
            except OSError:
                if backup.exists():
                    backup.rename(destination)
                raise
        finally:
            OUT = original_out

if __name__ == "__main__":
    try:
        main()
    except (ImportFailure, OSError, ValueError) as error:
        sys.exit(f"Build failed: {error}. Fix the input and retry; previous output was retained.")
