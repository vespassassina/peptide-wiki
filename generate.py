#!/usr/bin/env python3
"""Generates the Peptide Wiki static HTML site, styled with artifactkit
(https://github.com/vespassassina/artifactkit) — peptides.json / categories.json
are the data; this script renders the ak-* component vocabulary around them."""
import json, os, html, shutil, re
from datetime import date

SITE_DOMAIN = "https://peptide-wiki.local"
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
SITE_NAME = "Peptide Wiki"
SITE_DESC = "A reference on commonly discussed peptides: mechanism, research status, dosing protocols from the literature and from self-experimentation communities, and safety notes."

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
        <li><a href="/about.html"{cur("about")}>About</a></li>
      </ul>
      <form class="site-search" role="search" action="/directory.html" method="get">
        <label for="topSearch" class="visually-hidden">Search peptides</label>
        <input class="ak-input" type="search" id="topSearch" name="q" placeholder="Search peptides…" autocomplete="off">
        <button class="ak-btn" type="submit">Search</button>
      </form>
    </nav>
  </div>
</header>'''

def site_footer():
    return f'''<footer class="ak-footer">
  <p><strong>Not medical advice.</strong> This wiki summarizes published research, regulatory status and self-reported community experience for informational purposes only. Many compounds described here are unapproved research chemicals with limited or no human safety data. Consult a licensed physician before starting, stopping or combining any of these substances. See <a href="/about.html">about &amp; disclaimer</a>.</p>
  <p class="ak-small">Last updated {TODAY} · styled with <a href="https://github.com/vespassassina/artifactkit">artifactkit</a> · machine-readable index: <a href="/data/peptides.json">/data/peptides.json</a> · <a href="/sitemap.xml">/sitemap.xml</a> · <a href="/llms.txt">/llms.txt</a></p>
</footer>'''

def breadcrumbs(items):
    lis, ld_items = [], []
    for i, (label, href) in enumerate(items, start=1):
        if href:
            lis.append(f'<li><a href="{esc(href)}">{esc(label)}</a></li>')
        else:
            lis.append(f'<li aria-current="page">{esc(label)}</li>')
        ld_items.append({"@type": "ListItem", "position": i, "name": label, **({"item": "https://peptide-wiki.local" + href} if href else {})})
    ld = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": ld_items})
    return f'<ol class="ak-breadcrumb">{"".join(lis)}</ol>\n<script type="application/ld+json">{ld}</script>'

def page(title, description, active, body, canonical="", page_id="page", extra_scripts=""):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · {esc(SITE_NAME)}</title>
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
<script>ak.init({{ id: "peptide-wiki-{esc(page_id)}", title: {json.dumps(title)} }});</script>
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

def related_list(slugs):
    items = [f'<li><a href="/peptides/{s}.html" rel="related">{esc(PEPTIDES[s]["name"])}</a></li>' for s in slugs if s in PEPTIDES]
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
    items = [f'<li><a href="/stacks/{s}.html" rel="related">{esc(STACKS[s]["title"])}</a></li>' for s in slugs if s in STACKS]
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

def peptide_page(slug, p):
    cats = p["categories"]
    primary_cat = cats[0]
    aliases = ", ".join(p.get("aliases", [])) or "—"
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "MedicalWebPage", "name": p["name"],
        "alternateName": p.get("aliases", []), "description": p["tagline"],
        "about": {"@type": "Drug", "name": p["name"], "alternateName": p.get("aliases", [])},
        "medicalAudience": "Patient", "lastReviewed": TODAY,
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
    <span class="ak-asof">Reviewed {TODAY}</span>
    {fav_button(f"peptide:{slug}", p["name"])}
  </div>
</header>

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
      <li><a href="#origin">Origin</a></li>
      <li><a href="#mechanism">Mechanism</a></li>
      <li><a href="#research">Research summary</a></li>
      <li><a href="#citations">Citations</a></li>
      <li><a href="#benefits">Reported benefits</a></li>
      <li><a href="#dosing">Dosing protocols</a></li>
      <li><a href="#side-effects">Side effects</a></li>
      <li><a href="#safety">Safety notes</a></li>
      <li><a href="#community">Community &amp; reddit notes</a></li>
      <li><a href="#related">Related peptides</a></li>
      {'<li><a href="#stacks">Used in stacks</a></li>' if slug in PEPTIDE_STACKS else ''}
      {'<li><a href="#mixing">Mixing compatibility</a></li>' if p.get("mixing_notes") or p.get("mixing_caution") else ''}
    </ul>
  </nav>

  <article class="ak-prose">
    <section id="origin" class="ak-section"><h2>Origin</h2><p>{esc(p["origin"])}</p></section>
    <section id="mechanism" class="ak-section"><h2>Mechanism</h2><p>{esc(p["mechanism"])}</p></section>

    <section id="research" class="ak-section">
      <h2>Research summary</h2>
      <div class="ak-exhibit">
        <p class="ak-eyebrow">Evidence</p>
        <p class="ak-takeaway">{esc(p["research_summary"])}</p>
        <p class="ak-source">Evidence tier: {pill(slug)} — see the <a href="/about.html">methodology note</a> for how this is assessed.</p>
      </div>
    </section>

    <section id="citations" class="ak-section">
      <h2>Citations</h2>
      {citations_block(p.get("citations", []))}
    </section>

    <section id="benefits" class="ak-section"><h2>Reported benefits</h2>{ul(p["reported_benefits"])}</section>

    <section id="dosing" class="ak-section">
      <h2>Dosing protocols reported in the literature &amp; community</h2>
      <p class="ak-small">These are protocols reported by compounding pharmacies, published trials, or self-experimentation communities — not a prescription. Start low, especially for anything new.</p>
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

    <section id="related" class="ak-section"><h2>Related peptides</h2>{related_list(p.get("related", []))}</section>

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
    ld = json.dumps({
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
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "MedicalWebPage", "name": s["title"],
        "description": s["tagline"], "lastReviewed": TODAY,
    })
    body = f'''{crumbs}
<article itemscope itemtype="https://schema.org/MedicalWebPage" data-stack-slug="{esc(slug)}">
<header class="ak-pagehead">
  <div>
    <p class="ak-eyebrow">Peptide stack</p>
    <h1 itemprop="name">{esc(s["title"])}</h1>
    <p class="ak-lede" itemprop="description">{esc(s["tagline"])}</p>
    <p class="peptide-pills"><span class="ak-pill {cls}">{esc(label)}</span></p>
  </div>
  <div class="ak-meta">
    <span class="ak-asof">Reviewed {TODAY}</span>
    {fav_button(f"stack:{slug}", s["title"])}
  </div>
</header>

<div class="ak-banner"><strong>Not a recommendation.</strong> This page explains why a combination is discussed together in research or community circles — it is not an endorsement of stacking these compounds. See each component's own page for full detail, dosing and safety notes.</div>

<h2 class="ak-sechead"><span class="ak-n">COMPONENTS</span> in this stack</h2>
{stack_component_cards(s["component_slugs"])}

<article class="ak-prose">
  <section class="ak-section"><h2>Why these are combined</h2><p>{esc(s["rationale"])}</p></section>

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
    n_approved = sum(1 for s in ALL_SLUGS if tier(s)[0] == "ak-pill-ok")
    n_research = sum(1 for s in ALL_SLUGS if tier(s)[0] == "ak-pill-off")
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "description": SITE_DESC, "url": "/index.html",
        "potentialAction": {"@type": "SearchAction", "target": "/directory.html?q={search_term}", "query-input": "required name=search_term"}
    })
    body = f'''<section class="hero">
  <p class="ak-eyebrow">Peptide reference</p>
  <h1>{esc(SITE_NAME)}</h1>
  <p class="ak-lede">{esc(SITE_DESC)}</p>
  <form class="hero-search" role="search" action="/directory.html" method="get">
    <label for="heroSearch" class="visually-hidden">Search peptides</label>
    <input class="ak-input" type="search" id="heroSearch" name="q" placeholder="Search by name, e.g. BPC-157…" autocomplete="off">
    <button class="ak-btn ak-btn-primary" type="submit">Search</button>
  </form>
</section>

<div class="ak-kpis ak-cols-4">
  <div class="ak-kpi"><span class="ak-k">Peptides catalogued</span><span class="ak-v">{len(PEPTIDES)}</span></div>
  <div class="ak-kpi"><span class="ak-k">Benefit categories</span><span class="ak-v">{len(CATEGORIES)}</span></div>
  <div class="ak-kpi"><span class="ak-k">FDA-approved drugs</span><span class="ak-v">{n_approved}</span><span class="ak-d">included for comparison</span></div>
  <div class="ak-kpi"><span class="ak-k">Research chemicals</span><span class="ak-v">{n_research}</span><span class="ak-d">no regulatory approval</span></div>
</div>

<h2 class="ak-sechead"><span class="ak-n">BROWSE</span> by benefit</h2>
<ul class="card-grid">{cat_cards}</ul>

<div class="ak-exhibit">
  <p class="ak-eyebrow">How this wiki is organized</p>
  <p>Every peptide has one canonical <a href="/directory.html">leaf page</a> with full detail: origin, mechanism, a plain-language research summary, reported benefits, dosing protocols pulled from compounding-pharmacy guides and published trials, side effects, safety notes, and a clearly-labelled community/anecdotal-experience section sourced from self-experimentation communities. Category hub pages summarize and link to the peptides relevant to that goal — a peptide can appear in more than one category (GHK-Cu, for example, is both an anti-aging and a recovery peptide) but its full detail lives in exactly one place.</p>
  <p class="ak-source">For machines: every page carries JSON-LD structured data (MedicalWebPage/CollectionPage plus BreadcrumbList), and the whole dataset is available as flat JSON at <a href="/data/peptides.json">/data/peptides.json</a> and <a href="/data/categories.json">/data/categories.json</a>, with a sitemap at <a href="/sitemap.xml">/sitemap.xml</a> and an <a href="/llms.txt">/llms.txt</a> summary for LLM agents.</p>
</div>

<h2 class="ak-sechead"><span class="ak-n">START</span> here</h2>
<ul>
  <li><a href="/dosing-safety.html">Dosing, reconstitution &amp; safety guide</a> — reconstitution math, storage, injection basics, general risk framing.</li>
  <li><a href="/stacks.html">Peptide stacks</a> — commonly combined peptides, with rationale, evidence level and links back to each component.</li>
  <li><a href="/glossary.html">Glossary</a> — GHRP, GHRH, DAC, half-life and other recurring terms explained once.</li>
  <li><a href="/directory.html">Full directory</a> — every peptide in one sortable, filterable table.</li>
  <li><a href="/about.html">About &amp; disclaimer</a> — sourcing, limitations, and why this is not medical advice.</li>
</ul>
<script type="application/ld+json">{ld}</script>'''
    return page(SITE_NAME, SITE_DESC, "home", body, canonical="/index.html", page_id="home")

# ---------- directory page ----------
def directory_page():
    rows = []
    for s in ALL_SLUGS:
        p = PEPTIDES[s]
        cls, label = tier(s)
        cat_badges = "".join(f'<a class="ak-badge" href="/categories/{c}.html">{esc(CATEGORIES[c]["name"])}</a> ' for c in p["categories"])
        rows.append(f'''<tr>
<td data-v="{esc(p["name"])}"><a href="/peptides/{s}.html">{esc(p["name"])}</a><br><span class="ak-small">{esc(", ".join(p.get("aliases", [])[:2]))}</span></td>
<td>{cat_badges}</td>
<td>{esc(p["tagline"])}</td>
<td data-v="{esc(label)}"><span class="ak-pill {cls}">{esc(label)}</span></td>
</tr>''')
    body = f'''{breadcrumbs([("Home", "/index.html"), ("Directory", None)])}
<header class="ak-pagehead">
  <div>
    <p class="ak-eyebrow">Reference</p>
    <h1>Full peptide directory</h1>
    <p class="ak-lede">All {len(PEPTIDES)} peptides in this wiki. Filter by name or alias, or click a column header to sort.</p>
  </div>
  <div class="ak-meta">{len(PEPTIDES)} entries</div>
</header>
<div class="ak-toolbar dir-controls">
  <label for="dirFilter" class="visually-hidden">Filter directory</label>
  <input class="ak-input" type="search" id="dirFilter" placeholder="Filter by name, alias or status…" autocomplete="off">
</div>
<div class="ak-tblwrap">
<table class="ak-table" id="directoryTable">
<caption class="ak-vh">Peptide directory</caption>
<thead><tr>
  <th scope="col" data-sort="s">Peptide</th>
  <th scope="col">Categories</th>
  <th scope="col">Summary</th>
  <th scope="col" data-sort="s">Status</th>
</tr></thead>
<tbody>{"".join(rows)}</tbody>
</table>
</div>
<p class="ak-empty" id="noResults" data-ak-empty hidden>No peptides match your filter.</p>'''
    extra = '''<script>
(function(){
  var t = ak.table(document.getElementById('directoryTable'), { filterInput: '#dirFilter' });
  var params = new URLSearchParams(window.location.search);
  var q = params.get('q');
  if (q) { document.getElementById('dirFilter').value = q; t.filter(q); }
})();
</script>'''
    return page("Full directory", "Every peptide in this wiki, sortable and filterable by name, alias and status.", "directory", body, canonical="/directory.html", page_id="directory", extra_scripts=extra)

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

# ---------- about ----------
def about_page():
    body = f'''{breadcrumbs([("Home", "/index.html"), ("About", None)])}
<header class="ak-pagehead"><div><p class="ak-eyebrow">Reference</p><h1>About &amp; disclaimer</h1></div></header>
<article class="ak-prose">
<section class="ak-section"><h2>What this is</h2>
<p>A self-contained reference on commonly discussed peptides, organized by the benefit people most often seek them for (recovery, anti-aging, longevity, fat loss, fitness, sexual health, cognition). It combines: published pharmacology and clinical-trial research where it exists, regulatory/approval status, dosing protocols reported by compounding pharmacies and self-experimentation communities, and anecdotal community experience, kept clearly labelled and separated from the clinical-evidence sections.</p>
</section>
<section class="ak-section"><h2>This is not medical advice</h2>
<div class="ak-banner ak-banner-bad">Nothing on this site is a recommendation to use, or a guide to using, any specific substance. Many peptides described here are unapproved research chemicals sold "not for human consumption," with limited to no human safety or efficacy data at the doses commonly self-administered. Always consult a licensed physician before starting, stopping, or combining any of these substances.</div>
</section>
<section class="ak-section"><h2>Evidence-tier legend</h2>
<p>Every peptide carries one status pill, used consistently across the directory, category pages and leaf pages:</p>
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
    return page("About & disclaimer", "Methodology, sourcing and the disclaimer governing this peptide wiki.", "about", body, canonical="/about.html", page_id="about")

# ---------- favorites (client-side, cookie-backed) ----------
def favorites_page():
    peptide_index = [
        {"slug": s, "name": PEPTIDES[s]["name"], "tagline": PEPTIDES[s]["tagline"],
         "pillClass": tier(s)[0], "pillLabel": tier(s)[1]}
        for s in ALL_SLUGS
    ]
    stack_index = [
        {"slug": s, "title": STACKS[s]["title"], "tagline": STACKS[s]["tagline"],
         "pillClass": EVIDENCE_LEVEL_PILL.get(STACKS[s]["evidence_level"], ("ak-pill-off", ""))[0],
         "pillLabel": EVIDENCE_LEVEL_PILL.get(STACKS[s]["evidence_level"], ("", "Unclear"))[1]}
        for s in ALL_STACK_SLUGS
    ]
    body = f'''{breadcrumbs([("Home", "/index.html"), ("Favorites", None)])}
<header class="ak-pagehead">
  <div>
    <p class="ak-eyebrow">Your list</p>
    <h1>★ Favorites</h1>
    <p class="ak-lede">Peptides and stacks you've starred, kept in a cookie in this browser. Nothing is sent anywhere — clearing cookies or switching browsers clears this list.</p>
  </div>
</header>
<div id="favoritesRoot">
  <p class="ak-small">Loading…</p>
</div>
<script type="application/json" id="pwPeptideIndex">{json.dumps(peptide_index)}</script>
<script type="application/json" id="pwStackIndex">{json.dumps(stack_index)}</script>'''
    return page("Favorites", "Peptides and stacks you've starred, saved in a browser cookie.", "favorites", body, canonical="/favorites.html", page_id="favorites")

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
  var MAX_AGE = 60 * 60 * 24 * 400; // ~400 days, the practical cap most browsers allow

  function readFavorites(){
    try {
      var match = document.cookie.split('; ').find(function(row){ return row.indexOf(COOKIE + '=') === 0; });
      if (!match) return [];
      var raw = decodeURIComponent(match.split('=').slice(1).join('='));
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) { return []; }
  }

  function writeFavorites(list){
    try {
      document.cookie = COOKIE + '=' + encodeURIComponent(JSON.stringify(list)) + '; path=/; max-age=' + MAX_AGE + '; samesite=lax';
    } catch (e) {}
  }

  function isFav(key){ return readFavorites().indexOf(key) !== -1; }

  function toggleFav(key){
    var list = readFavorites();
    var i = list.indexOf(key);
    if (i === -1) { list.push(key); } else { list.splice(i, 1); }
    writeFavorites(list);
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
        setButtonState(btn, toggleFav(key));
      });
    });
  });

  ak.renderFavorites = function(){
    var root = document.getElementById('favoritesRoot');
    if (!root) return;
    var peptideIndexEl = document.getElementById('pwPeptideIndex');
    var stackIndexEl = document.getElementById('pwStackIndex');
    var peptideIndex = peptideIndexEl ? JSON.parse(peptideIndexEl.textContent) : [];
    var stackIndex = stackIndexEl ? JSON.parse(stackIndexEl.textContent) : [];
    var favs = readFavorites();
    var favPeptides = favs.filter(function(k){ return k.indexOf('peptide:') === 0; })
      .map(function(k){ return k.slice(8); });
    var favStacks = favs.filter(function(k){ return k.indexOf('stack:') === 0; })
      .map(function(k){ return k.slice(6); });
    var peptides = peptideIndex.filter(function(p){ return favPeptides.indexOf(p.slug) !== -1; });
    var stacks = stackIndex.filter(function(s){ return favStacks.indexOf(s.slug) !== -1; });

    if (peptides.length === 0 && stacks.length === 0) {
      root.innerHTML = '<p class="ak-empty">No favorites yet. Open any peptide or stack page and click "Add to favorites".</p>';
      return;
    }

    function card(href, title, tagline, pillClass, pillLabel){
      return '<li><a class="card-link" href="' + href + '"><h3>' + title + '</h3><p>' + tagline +
        '</p><span class="ak-pill ' + pillClass + '">' + pillLabel + '</span></a></li>';
    }

    var html = '';
    if (peptides.length) {
      html += '<h2 class="ak-sechead"><span class="ak-n">PEPTIDES</span></h2><ul class="card-grid">';
      peptides.forEach(function(p){
        html += card('/peptides/' + p.slug + '.html', p.name, p.tagline, p.pillClass, p.pillLabel);
      });
      html += '</ul>';
    }
    if (stacks.length) {
      html += '<h2 class="ak-sechead"><span class="ak-n">STACKS</span></h2><ul class="card-grid">';
      stacks.forEach(function(s){
        html += card('/stacks/' + s.slug + '.html', s.title, s.tagline, s.pillClass, s.pillLabel);
      });
      html += '</ul>';
    }
    root.innerHTML = html;
  };

  document.addEventListener('DOMContentLoaded', function(){ ak.renderFavorites(); });
})();
"""

def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)

    write("index.html", home_page())
    write("directory.html", directory_page())
    write("glossary.html", glossary_page())
    write("dosing-safety.html", dosing_safety_page())
    write("about.html", about_page())
    write("favorites.html", favorites_page())
    for cslug, c in CATEGORIES.items():
        write(f"categories/{cslug}.html", category_page(cslug, c))
    for slug, p in PEPTIDES.items():
        write(f"peptides/{slug}.html", peptide_page(slug, p))
    write("stacks.html", stacks_index_page())
    for slug, s in STACKS.items():
        write(f"stacks/{slug}.html", stack_page(slug, s))

    # vendor artifactkit assets + our site chrome
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    for fname in ["theme.css", "components.css", "print.css", "core.js", "site.css"]:
        shutil.copy(os.path.join(VENDOR, fname), os.path.join(OUT, "assets", fname))
    write("assets/site.js", SITE_JS)

    # machine-readable data
    write("data/peptides.json", json.dumps(PEPTIDES, indent=2))
    write("data/categories.json", json.dumps(CATEGORIES, indent=2))
    write("data/stacks.json", json.dumps(STACKS, indent=2))
    sitemap_urls = ["/index.html", "/directory.html", "/glossary.html", "/dosing-safety.html", "/about.html", "/stacks.html"]
    sitemap_urls += [f"/categories/{c}.html" for c in CATEGORIES]
    sitemap_urls += [f"/peptides/{s}.html" for s in ALL_SLUGS]
    sitemap_urls += [f"/stacks/{s}.html" for s in ALL_STACK_SLUGS]
    write("data/sitemap.json", json.dumps({"site": SITE_NAME, "generated": TODAY, "pages": sitemap_urls, "categories": {c: CAT_PEPTIDES.get(c, []) for c in CATEGORIES}}, indent=2))

    xml_urls = "".join(f"<url><loc>{u}</loc></url>" for u in sitemap_urls)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{xml_urls}</urlset>')

    lines = [f"# {SITE_NAME}", "", SITE_DESC, "", "## Categories"]
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

    print(f"Generated {len(PEPTIDES)} peptide pages, {len(CATEGORIES)} category pages, plus core pages into {OUT}")

if __name__ == "__main__":
    main()
