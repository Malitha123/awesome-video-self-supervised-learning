from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from repo_tools import (
    ROOT, MEDIA_DIR, README_PATH, SITE_URL, REPO_URL, load_papers,
    normalize_venue, replace_representation_section,
    replace_representation_year_links, remove_visible_keyword_list,
    remove_challenges_section, stats,
)

MEDIA_DIR.mkdir(exist_ok=True)

INITIAL_REVIEW_DATE = "2026-08-11"
SEO_DATASETS = [
    "UCF101", "HMDB51", "Kinetics-400", "Kinetics-600", "Kinetics-700",
    "Something-Something V1", "Something-Something V2", "Diving48",
    "EPIC-KITCHENS", "AVA", "FineGYM", "Charades", "Ego4D",
]
SEO_TOPICS = [
    "video self-supervised learning", "Video SSL", "VideoSSL",
    "self-supervised video learning", "self-supervised video representation learning",
    "masked video modeling", "video representation pretraining",
]
SEO_VENUES = ["CVPR", "ICCV", "ECCV", "NeurIPS", "ICLR", "AAAI", "WACV"]

FAQ_ITEMS = [
    (
        "What is video self-supervised learning?",
        "Video self-supervised learning learns useful spatial and temporal representations from videos without requiring a manually annotated label for every training example. Common objectives include masked reconstruction, contrastive learning, temporal prediction, motion modeling and cross-modal learning.",
    ),
    (
        "What do Video SSL, VideoSSL and SSL video mean?",
        "Video SSL and VideoSSL are common abbreviations for video self-supervised learning. SSL video is another search phrasing for the same research area, which is also described as self-supervised video representation learning or video representation pretraining.",
    ),
    (
        "Which publication metadata is shown?",
        "Each catalog entry displays its confirmed publication year and latest verified venue, alongside the title, authors and research links.",
    ),
    (
        "How are later conference or journal publications handled?",
        "When a preprint is later published at a conference or journal, the public entry is updated to the latest confirmed venue while the supporting audit record remains in the repository.",
    ),
]


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def publication_review_date(papers: list[dict]) -> tuple[str, str]:
    dates = [str(paper.get("audited_at", "")) for paper in papers]
    valid = []
    for value in dates:
        try:
            datetime.strptime(value, "%Y-%m-%d")
            valid.append(value)
        except ValueError:
            continue
    iso_date = max(valid, default=INITIAL_REVIEW_DATE)
    parsed = datetime.strptime(iso_date, "%Y-%m-%d")
    display = f"{parsed.day} {parsed.strftime('%B %Y')}"
    return iso_date, display


def save_bar_chart(path: Path, title: str, labels: list[str], values: list[int], horizontal=False, xlabel="Number of papers"):
    plt.rcParams.update({
        "font.size": 10,
        "axes.titlesize": 14,
        "axes.labelsize": 10,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#d6e3f0",
        "savefig.facecolor": "white",
    })
    height = max(4.6, min(6.2, 2.8 + len(labels) * 0.27)) if horizontal else 4.6
    fig, ax = plt.subplots(figsize=(9.1, height))
    color = "#2878c8"
    grid = "#e8f0f8"
    text = "#17324a"
    if horizontal:
        labels_r = labels[::-1]
        values_r = values[::-1]
        ax.barh(labels_r, values_r, color=color)
        ax.set_xlabel(xlabel)
        ax.grid(axis="x", color=grid, linewidth=1)
        top = max(values_r or [1])
        for i, v in enumerate(values_r):
            ax.text(v + top * 0.012, i, str(v), va="center", color=text)
    else:
        ax.bar(labels, values, color=color)
        ax.set_ylabel(xlabel)
        ax.grid(axis="y", color=grid, linewidth=1)
        top = max(values or [1])
        for i, v in enumerate(values):
            ax.text(i, v + top * 0.015, str(v), ha="center", va="bottom", color=text)
    ax.set_title(title)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, format="svg", bbox_inches="tight")
    plt.close(fig)


def generate_charts(s: dict):
    years = list(s["year_counts"].keys())
    yvals = list(s["year_counts"].values())
    save_bar_chart(MEDIA_DIR / "stats_papers_by_year.svg", "Papers by Year", [str(y) for y in years], yvals)

    venue_rows = s["venue_counts_top"]
    save_bar_chart(MEDIA_DIR / "stats_papers_by_venue.svg", "Papers by Venue", [x[0] for x in venue_rows], [x[1] for x in venue_rows], horizontal=True)


def stats_markdown(s: dict) -> str:
    return f'''## Repository Statistics

The charts below summarize the canonical collection by publication year and venue. Additional research metadata remains available in the repository data files but is intentionally omitted from the public catalog and README.

<div class="stats-kpis">
  <div><strong>{s['papers_tracked']}</strong><span>representation-learning papers</span></div>
  <div><strong>{s['years_covered']}</strong><span>years covered</span></div>
  <div><strong>{s['distinct_normalized_venues']}</strong><span>normalized venues</span></div>
</div>

<div class="stats-grid">
  <figure><img src="./media/stats_papers_by_year.svg" alt="Bar chart showing the number of VideoSSL papers by year"><figcaption>Papers by year</figcaption></figure>
  <figure><img src="./media/stats_papers_by_venue.svg" alt="Bar chart showing the number of VideoSSL papers by publication venue"><figcaption>Papers by venue</figcaption></figure>
</div>
'''


def parse_markdown_entries(text: str, start_heading: str, end_heading: str) -> list[dict]:
    m = re.search(re.escape(start_heading) + r"\n(.*?)(?=\n" + re.escape(end_heading) + r"\n)", text, flags=re.S)
    if not m:
        return []
    section = m.group(1)
    lines = section.splitlines()
    out = []
    i = 0
    while i < len(lines):
        sm = re.match(r"\s*-\s*\*\*(.*?)\*\*\s*\(([^)]*)\)\s*<br>", lines[i].strip())
        if not sm:
            i += 1
            continue
        title, date_label = sm.group(1).strip(), sm.group(2).strip()
        block = []
        j = i + 1
        while j < len(lines) and not re.match(r"\s*-\s*\*\*", lines[j].strip()):
            if lines[j].strip():
                block.append(lines[j].strip())
            j += 1
        venue = ""
        authors = ""
        links = []
        for line in block:
            vm = re.match(r"\*(.*?)\*\s*<br>", line)
            if vm and not venue:
                venue = vm.group(1).strip()
                continue
            if "[[" in line:
                links.extend(re.findall(r"\[\[([^\]]+)\]\]\(([^)]+)\)", line))
                continue
            if venue and not authors and not line.startswith("<!--"):
                authors = line.replace("<br>", "").strip()
        out.append({"title": title, "date_label": date_label, "venue": venue, "authors_display": authors, "links": links})
        i = j
    return out


def resource_card(e: dict) -> str:
    links = "".join(f'<a href="{esc(url)}">{esc(label)}</a>' for label, url in e.get("links", []))
    return f'''<article class="resource-card">
      <div class="resource-meta">{esc(e.get('date_label'))} · {esc(e.get('venue'))}</div>
      <h3>{esc(e.get('title'))}</h3>
      <p>{esc(e.get('authors_display'))}</p>
      <div class="card-links">{links}</div>
    </article>'''


def paper_card(p: dict, idx: int) -> str:
    authors = p.get("authors_display") or ", ".join(p.get("authors") or [])
    links = []
    if p.get("paper_url"):
        links.append(f'<a class="paper-link" href="{esc(p["paper_url"])}">Paper</a>')
    if p.get("code_url"):
        links.append(f'<a href="{esc(p["code_url"])}">Code</a>')
    if p.get("project_url"):
        links.append(f'<a href="{esc(p["project_url"])}">Project</a>')
    data_search = " ".join([
        p.get("title", ""), authors, p.get("venue", ""), p.get("venue_normalized", ""),
        str(p.get("year", ""))
    ]).lower()
    return f'''<article class="paper-card" data-index="{idx}" data-search="{esc(data_search)}" data-year="{esc(p.get('year'))}" data-venue="{esc(p.get('venue_normalized') or p.get('venue'))}">
      <div class="paper-topline"><span class="year-badge">{esc(p.get('year'))}</span><span class="venue-badge">{esc(p.get('venue_normalized') or p.get('venue'))}</span></div>
      <h3>{esc(p.get('title'))}</h3>
      <p class="authors">{esc(authors)}</p>
      <div class="paper-bottom"><div class="card-links">{' '.join(links)}</div></div>
    </article>'''


def options(values: list[str], label: str) -> str:
    return f'<option value="">{esc(label)}</option>' + "".join(f'<option value="{esc(v)}">{esc(v)}</option>' for v in values)


def faq_html() -> str:
    items = "".join(
        f'<details{" open" if i == 0 else ""}><summary>{esc(question)}</summary><p>{esc(answer)}</p></details>'
        for i, (question, answer) in enumerate(FAQ_ITEMS)
    )
    return f'''<section id="video-ssl-faq" class="section-block faq-section">
      <div class="section-heading"><div><span class="section-kicker">Field guide</span><h2>Video self-supervised learning FAQ</h2></div></div>
      <div class="faq-grid">{items}</div>
    </section>'''


def site_template(papers: list[dict], s: dict, readme: str) -> str:
    review_date_iso, review_date_display = publication_review_date(papers)
    papers_sorted = sorted(papers, key=lambda p: (-int(p.get("year") or 0), p.get("source_order") if p.get("source_order") is not None else -1, p.get("title", "").lower()))
    paper_cards = "\n".join(paper_card(p, i) for i, p in enumerate(papers_sorted))
    years = sorted({str(p.get("year")) for p in papers if p.get("year")}, reverse=True)
    venues = sorted({p.get("venue_normalized") or normalize_venue(p.get("venue", "")) for p in papers if p.get("venue")})
    year_counts = {str(k): v for k, v in s["year_counts"].items()}
    year_tiles = "".join(
        f'<button class="year-tile" data-set-year="{y}"><strong>{y}</strong><span>{year_counts.get(y, 0)} paper{"" if year_counts.get(y, 0) == 1 else "s"}</span></button>'
        for y in years
    )

    surveys = parse_markdown_entries(readme, "#  Surveys", "# Benchmarking")
    benchmarking = parse_markdown_entries(readme, "# Benchmarking", "# Representation Learning")
    surveys_html = "".join(resource_card(e) for e in surveys[:4])
    bench_html = "".join(resource_card(e) for e in benchmarking[:8])

    page_title = "Video SSL Papers by Year & Venue | Awesome VideoSSL"
    page_modified = datetime.now(timezone.utc).date().isoformat()
    desc = (
        f"Browse {s['papers_tracked']} Video SSL and self-supervised video learning papers "
        "by verified year and venue, covering UCF101, HMDB51, Kinetics and more."
    )
    paper_schema_items = []
    for position, p in enumerate(papers_sorted, start=1):
        article = {
            "@type": "ScholarlyArticle",
            "name": p.get("title", ""),
            "headline": p.get("title", ""),
            "datePublished": str(p.get("year", "")),
            "author": [
                {"@type": "Person", "name": author}
                for author in (p.get("authors") or [])
                if author
            ],
            "isPartOf": {
                "@type": "CreativeWork",
                "name": p.get("venue_normalized") or p.get("venue", ""),
            },
        }
        if p.get("paper_url"):
            article["url"] = p["paper_url"]
        paper_schema_items.append({"@type": "ListItem", "position": position, "item": article})

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{SITE_URL}#website",
                "url": SITE_URL,
                "name": "Awesome Video Self-Supervised Learning",
                "alternateName": ["Awesome VideoSSL", "Video SSL Papers"],
                "inLanguage": "en",
            },
            {
                "@type": "CollectionPage",
                "@id": f"{SITE_URL}#collection",
                "url": SITE_URL,
                "name": page_title,
                "headline": "Video SSL and Self-Supervised Video Learning Papers by Year and Venue",
                "description": desc,
                "dateModified": page_modified,
                "inLanguage": "en",
                "isPartOf": {"@id": f"{SITE_URL}#website"},
                "author": [
                    {"@type": "Person", "name": "Ishan Dave", "url": "https://daveishan.github.io/"},
                    {"@type": "Person", "name": "Malitha Gunawardhana", "url": "https://malitha123.github.io/malitha/"},
                ],
                "about": [
                    {"@type": "Thing", "name": term}
                    for term in SEO_TOPICS + SEO_DATASETS + SEO_VENUES
                ],
                "keywords": SEO_TOPICS + SEO_DATASETS + SEO_VENUES,
                "mainEntity": [
                    {"@id": f"{SITE_URL}#paper-list"},
                    {"@id": f"{SITE_URL}#faq"},
                ],
            },
            {
                "@type": "ItemList",
                "@id": f"{SITE_URL}#paper-list",
                "name": "Video self-supervised learning paper collection",
                "numberOfItems": s["papers_tracked"],
                "itemListOrder": "https://schema.org/ItemListOrderDescending",
                "itemListElement": paper_schema_items,
            },
            {
                "@type": "FAQPage",
                "@id": f"{SITE_URL}#faq",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": question,
                        "acceptedAnswer": {"@type": "Answer", "text": answer},
                    }
                    for question, answer in FAQ_ITEMS
                ],
            },
        ],
    }
    schema_json = json.dumps(schema, ensure_ascii=False).replace("</", "<\\/")

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(page_title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<link rel="canonical" href="{SITE_URL}">
<link rel="manifest" href="./site.webmanifest">
<meta property="og:type" content="website"><meta property="og:site_name" content="Awesome VideoSSL"><meta property="og:locale" content="en_US"><meta property="og:title" content="{esc(page_title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{SITE_URL}"><meta property="og:image" content="{SITE_URL}media/video_ssl_families.png"><meta property="og:image:width" content="800"><meta property="og:image:height" content="500"><meta property="og:image:alt" content="Overview of video self-supervised learning research families">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(page_title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{SITE_URL}media/video_ssl_families.png"><meta name="twitter:image:alt" content="Overview of video self-supervised learning research families">
<meta name="theme-color" content="#f7fbff">
<script type="application/ld+json">{schema_json}</script>
<script>document.documentElement.classList.add('js')</script>
<style>
:root{{--bg:#f5f9fd;--panel:#fff;--soft:#eef6ff;--text:#17324a;--muted:#60758a;--accent:#0e74d7;--accent2:#095ca8;--line:#d8e6f2;--shadow:0 14px 34px rgba(18,69,117,.07);--max:1620px}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:linear-gradient(180deg,#fbfdff 0,#f2f8fe 38%,#f7fafc 100%);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.58}}a{{color:var(--accent);text-decoration:none}}a:hover{{text-decoration:underline}}a:focus-visible,button:focus-visible,select:focus-visible,input:focus-visible,summary:focus-visible{{outline:3px solid #73b6f1;outline-offset:3px}}button,select,input{{font:inherit}}.skip{{position:absolute;left:-9999px}}.skip:focus{{left:1rem;top:1rem;background:#fff;color:#000;padding:.5rem;z-index:30}}
.shell{{width:min(96vw,var(--max));margin-inline:auto}}.site-header{{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.93);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}}.nav{{display:flex;align-items:center;gap:1.05rem;padding:.82rem 0}}.brand{{font-weight:850;color:#17324a;margin-right:auto}}.nav a{{font-size:.94rem;color:#405b73}}.gh{{border:1px solid #c8dbea;border-radius:10px;padding:.4rem .72rem;background:#fff}}
.hero{{padding:4.8rem 0 2.4rem}}.eyebrow,.section-kicker{{font-size:.8rem;letter-spacing:.13em;text-transform:uppercase;color:#0e74d7;font-weight:800}}.hero h1{{font-size:clamp(2.7rem,5.1vw,5.35rem);line-height:1;letter-spacing:-.052em;margin:.6rem 0 1rem;max-width:1180px}}.hero h1 span{{color:#0e74d7}}.lead{{font-size:clamp(1.05rem,1.65vw,1.3rem);max-width:1060px;color:#4d657c}}.hero-actions{{display:flex;gap:.7rem;flex-wrap:wrap;margin-top:1.35rem}}.btn{{display:inline-block;padding:.74rem 1.02rem;border-radius:10px;font-weight:750;background:#0e74d7;color:#fff;border:0}}.btn.secondary{{background:#fff;color:#17324a;border:1px solid #c7dbea}}
.publication-notice{{display:grid;grid-template-columns:auto 1fr;gap:.9rem;align-items:start;margin:0 0 2.2rem;padding:1rem 1.15rem;background:#eef7ff;border:1px solid #bddbf3;border-left:5px solid var(--accent);border-radius:14px;box-shadow:0 10px 26px rgba(18,69,117,.05)}}.notice-mark{{display:grid;place-items:center;width:2rem;height:2rem;border-radius:50%;background:#0e74d7;color:#fff;font-weight:900;line-height:1}}.publication-notice h2{{font-size:1rem;line-height:1.35;margin:.05rem 0 .25rem;color:#17324a}}.publication-notice p{{margin:0;color:#47657e}}
.section-block{{padding:1.25rem 0 2rem;scroll-margin-top:5rem}}.section-heading{{display:flex;align-items:end;justify-content:space-between;gap:1rem;margin-bottom:1rem}}.section-heading h2{{font-size:clamp(1.75rem,2.3vw,2.4rem);line-height:1.1;margin:.25rem 0 0;letter-spacing:-.025em}}.section-heading p{{max-width:760px;color:var(--muted);margin:0}}
.stats-kpis{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem;margin:1rem 0 1.2rem}}.stats-kpis>div{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:1.05rem 1.15rem;box-shadow:var(--shadow)}}.stats-kpis strong{{display:block;font-size:2rem;line-height:1;color:#0e74d7}}.stats-kpis span{{display:block;color:#62778b;margin-top:.45rem;font-size:.92rem}}.stats-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}}.stats-grid figure{{margin:0;background:#fff;border:1px solid var(--line);border-radius:16px;padding:.85rem;box-shadow:var(--shadow)}}.stats-grid figcaption{{font-weight:800;margin:.35rem .25rem .1rem;color:#17324a}}.stats-grid img{{display:block;width:100%;height:auto}}
.scope-panel{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}}.scope-panel article{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:1.05rem 1.15rem;box-shadow:var(--shadow)}}.scope-panel h3{{font-size:1rem;margin:0 0 .45rem;color:#17324a}}.scope-panel p{{margin:0;color:#526a80;font-size:.92rem}}
.year-strip{{display:grid;grid-template-columns:repeat(11,minmax(0,1fr));gap:.55rem;margin-bottom:1rem}}.year-tile{{border:1px solid var(--line);background:#fff;border-radius:13px;padding:.75rem .4rem;cursor:pointer;color:#17324a;box-shadow:0 8px 22px rgba(18,69,117,.04)}}.year-tile:hover{{border-color:#89bdec;background:#f6fbff}}.year-tile strong{{display:block;font-size:1.05rem}}.year-tile span{{display:block;font-size:.76rem;color:var(--muted);margin-top:.15rem}}
.catalog-toolbar{{position:sticky;top:57px;z-index:12;background:rgba(245,249,253,.94);backdrop-filter:blur(12px);padding:.8rem 0;border-top:1px solid transparent;border-bottom:1px solid var(--line);margin-bottom:1rem}}.filter-grid{{display:grid;grid-template-columns:minmax(240px,2.1fr) repeat(2,minmax(150px,1fr));gap:.65rem}}.filter-grid input,.filter-grid select{{width:100%;background:#fff;color:#17324a;border:1px solid #c8dbea;border-radius:10px;padding:.72rem .78rem}}.catalog-meta{{display:flex;justify-content:space-between;align-items:center;gap:1rem;margin:.85rem 0;color:var(--muted);font-size:.92rem}}.clear-btn{{border:0;background:transparent;color:var(--accent);cursor:pointer;font-weight:700}}
.paper-grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1rem;align-items:stretch}}.paper-card{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:1rem;box-shadow:var(--shadow);display:flex;flex-direction:column;min-height:250px}}.paper-card:hover{{border-color:#b7d3eb;transform:translateY(-1px)}}.paper-topline{{display:flex;align-items:center;gap:.45rem;min-height:28px}}.year-badge{{font-weight:850;color:#0e74d7}}.venue-badge{{font-size:.76rem;border:1px solid #d9e6f2;border-radius:999px;padding:.18rem .48rem;color:#566f86;background:#f9fbfd;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:70%}}.paper-card h3{{font-size:1.03rem;line-height:1.32;margin:.72rem 0 .55rem;letter-spacing:-.012em}}.authors{{color:#61778b;font-size:.87rem;line-height:1.45;margin:0 0 .75rem;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}.paper-bottom{{display:flex;justify-content:flex-end;align-items:end;gap:.7rem;border-top:1px solid #edf2f7;margin-top:auto;padding-top:.72rem}}.card-links{{display:flex;gap:.55rem;flex-wrap:wrap;justify-content:flex-end;font-size:.84rem;font-weight:700}}.paper-link{{background:#edf6ff;border-radius:7px;padding:.24rem .45rem}}.js .paper-card.page-hidden,.js .paper-card.filter-hidden{{display:none}}
.pagination{{display:flex;justify-content:center;align-items:center;gap:.55rem;margin:1.4rem 0 .5rem}}.pagination button{{border:1px solid #c8dbea;background:#fff;color:#17324a;border-radius:9px;padding:.5rem .8rem;cursor:pointer}}.pagination button:disabled{{opacity:.42;cursor:default}}.page-status{{min-width:110px;text-align:center;color:var(--muted);font-size:.9rem}}
.resource-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}}.resource-card{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:1rem;box-shadow:var(--shadow)}}.resource-meta{{font-size:.78rem;color:#0e74d7;font-weight:800}}.resource-card h3{{font-size:1rem;line-height:1.35;margin:.55rem 0}}.resource-card p{{font-size:.87rem;color:#61778b;margin:.35rem 0 .75rem}}.faq-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.75rem}}details{{background:#fff;border:1px solid var(--line);border-radius:13px;padding:.9rem 1rem}}summary{{font-weight:800;cursor:pointer}}details p{{color:#526a80;margin:.65rem 0 0}}footer{{border-top:1px solid var(--line);color:#72869a;padding:2rem 0;text-align:center;background:#fbfdff;margin-top:2rem}}
@media(max-width:1400px){{.paper-grid{{grid-template-columns:repeat(3,minmax(0,1fr))}}.stats-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.year-strip{{grid-template-columns:repeat(6,minmax(0,1fr))}}}}@media(max-width:1050px){{.filter-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.filter-grid .search-field{{grid-column:1/-1}}.paper-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.resource-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.stats-kpis{{grid-template-columns:repeat(2,minmax(0,1fr))}}.scope-panel{{grid-template-columns:1fr}}}}@media(max-width:720px){{.shell{{width:min(94vw,var(--max))}}.nav a:not(.brand):not(.gh){{display:none}}.hero{{padding-top:3rem}}.hero h1{{font-size:2.65rem}}.paper-grid,.resource-grid,.faq-grid,.stats-grid{{grid-template-columns:1fr}}.filter-grid{{grid-template-columns:1fr}}.filter-grid .search-field{{grid-column:auto}}.year-strip{{grid-template-columns:repeat(3,minmax(0,1fr))}}.stats-kpis{{grid-template-columns:1fr 1fr}}.catalog-toolbar{{top:55px}}}}@media(max-width:520px){{.publication-notice{{grid-template-columns:1fr}}}}@media(max-width:460px){{.stats-kpis{{grid-template-columns:1fr}}}}@media(prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}*,*::before,*::after{{transition-duration:.01ms!important;animation-duration:.01ms!important;animation-iteration-count:1!important}}}}
</style>
</head>
<body>
<a class="skip" href="#catalog">Skip to paper catalog</a>
<header class="site-header"><nav class="nav shell" aria-label="Primary"><a class="brand" href="{SITE_URL}">Awesome VideoSSL</a><a href="#stats">Stats</a><a href="#coverage">Coverage</a><a href="#catalog">Browse papers</a><a href="#resources">Resources</a><a href="#video-ssl-faq">FAQ</a><a class="gh" href="{REPO_URL}">GitHub</a></nav></header>
<main class="shell">
<section class="hero">
  <div class="eyebrow">Research collection · maintained with the survey</div>
  <h1>Video SSL &amp; VideoSSL Papers <span>by Year &amp; Venue</span></h1>
  <p class="lead">A researcher-maintained catalog of video self-supervised learning and self-supervised video representation learning papers, organized by verified publication year and latest confirmed venue.</p>
  <div class="hero-actions"><a class="btn" href="#catalog">Explore the catalog</a><a class="btn secondary" href="{REPO_URL}">View repository</a></div>
</section>
<aside class="publication-notice" aria-labelledby="publication-review-title">
  <div class="notice-mark" aria-hidden="true">✓</div>
  <div><h2 id="publication-review-title">Publication status reviewed as of <time datetime="{review_date_iso}">{review_date_display}</time></h2><p>When an earlier arXiv manuscript was later published at a conference or in a journal, we updated its entry to the latest confirmed venue. If you find an incorrect record or a publication we missed, please <a href="{REPO_URL}/pulls">submit a GitHub pull request through the repository</a>.</p></div>
</aside>
<section id="stats" class="section-block">
  <div class="section-heading"><div><span class="section-kicker">Collection snapshot</span><h2>Repository statistics</h2></div><p>Public counts are generated from verified publication years and venues.</p></div>
  <div class="stats-kpis"><div><strong>{s['papers_tracked']}</strong><span>representation-learning papers</span></div><div><strong>{esc(s['years_covered'])}</strong><span>years covered</span></div><div><strong>{s['distinct_normalized_venues']}</strong><span>normalized venues</span></div></div>
  <div class="stats-grid"><figure><img src="./media/stats_papers_by_year.svg" alt="Bar chart of video self-supervised learning papers by publication year" loading="lazy" decoding="async"><figcaption>Papers by year</figcaption></figure><figure><img src="./media/stats_papers_by_venue.svg" alt="Bar chart of Video SSL papers by publication venue" loading="lazy" decoding="async"><figcaption>Papers by venue</figcaption></figure></div>
</section>
<section id="coverage" class="section-block">
  <div class="section-heading"><div><span class="section-kicker">Research coverage</span><h2>Video SSL terminology, datasets and venues</h2></div><p>The catalog keeps per-paper cards focused on year and venue while this overview explains the broader research scope.</p></div>
  <div class="scope-panel">
    <article><h3>Video self-supervised learning</h3><p>Video SSL, VideoSSL and SSL video research refer to self-supervised learning for video, including self-supervised video representation learning, video representation pretraining and masked video modeling.</p></article>
    <article><h3>Video understanding datasets</h3><p>The collection covers research using UCF101, HMDB51, Kinetics-400, Kinetics-600, Kinetics-700, Something-Something V1, Something-Something V2, Diving48, EPIC-KITCHENS, AVA, FineGYM, Charades, Ego4D and related datasets.</p></article>
    <article><h3>Conferences and journals</h3><p>Verified venues include CVPR, ICCV, ECCV, NeurIPS, ICLR, AAAI, WACV, ACM Multimedia, specialist workshops and peer-reviewed journals, with arXiv retained only when no later publication is confirmed.</p></article>
  </div>
</section>
<section id="catalog" class="section-block">
  <div class="section-heading"><div><span class="section-kicker">Interactive research index</span><h2>Browse the paper collection</h2></div><p>Filter the catalog instead of scrolling through a single long bibliography. The GitHub README keeps the traditional year-by-year list.</p></div>
  <div class="year-strip">{year_tiles}</div>
  <div class="catalog-toolbar"><div class="filter-grid"><input class="search-field" id="paper-search" type="search" placeholder="Search title, author, year or venue…" aria-label="Search papers"><select id="year-filter">{options(years,'All years')}</select><select id="venue-filter">{options(venues,'All venues')}</select></div></div>
  <div class="catalog-meta"><span id="result-count">{len(papers_sorted)} papers</span><button class="clear-btn" id="clear-filters" type="button">Clear filters</button></div>
  <div class="paper-grid" id="paper-grid">{paper_cards}</div>
  <div class="pagination"><button id="prev-page" type="button">Previous</button><span class="page-status" id="page-status">Page 1</span><button id="next-page" type="button">Next</button></div>
</section>
<section id="resources" class="section-block"><div class="section-heading"><div><span class="section-kicker">Surveys and evaluation</span><h2>Research resources</h2></div><p>Survey and benchmarking work that helps place individual methods in context.</p></div><div class="resource-grid">{surveys_html}{bench_html}</div></section>
{faq_html()}
</main>
<footer><div class="shell">Maintained as part of the <a href="{REPO_URL}">Awesome Video Self-Supervised Learning</a> research collection and its associated survey.</div></footer>
<script>
(() => {{
  const cards=[...document.querySelectorAll('.paper-card')];
  const search=document.getElementById('paper-search');
  const year=document.getElementById('year-filter');
  const venue=document.getElementById('venue-filter');
  const count=document.getElementById('result-count');
  const status=document.getElementById('page-status');
  const prev=document.getElementById('prev-page');
  const next=document.getElementById('next-page');
  const clear=document.getElementById('clear-filters');
  const pageSize=24;
  let page=1;

  function filteredCards() {{
    const q=(search.value||'').trim().toLowerCase();
    return cards.filter(card => {{
      const okSearch=!q || card.dataset.search.includes(q);
      const okYear=!year.value || card.dataset.year===year.value;
      const okVenue=!venue.value || card.dataset.venue===venue.value;
      const visible=okSearch&&okYear&&okVenue;
      card.classList.toggle('filter-hidden',!visible);
      return visible;
    }});
  }}

  function render() {{
    const visible=filteredCards();
    const pages=Math.max(1,Math.ceil(visible.length/pageSize));
    page=Math.min(page,pages);
    const start=(page-1)*pageSize, end=start+pageSize;
    cards.forEach(c=>c.classList.add('page-hidden'));
    visible.slice(start,end).forEach(c=>c.classList.remove('page-hidden'));
    count.textContent=`${{visible.length}} paper${{visible.length===1?'':'s'}}`;
    status.textContent=`Page ${{page}} of ${{pages}}`;
    prev.disabled=page<=1; next.disabled=page>=pages;
  }}

  [search,year,venue].forEach(el=>el.addEventListener('input',()=>{{page=1;render();}}));
  prev.addEventListener('click',()=>{{if(page>1){{page--;render();document.getElementById('catalog').scrollIntoView({{behavior:'smooth'}});}}}});
  next.addEventListener('click',()=>{{page++;render();document.getElementById('catalog').scrollIntoView({{behavior:'smooth'}});}});
  clear.addEventListener('click',()=>{{search.value='';year.value='';venue.value='';page=1;render();}});
  document.querySelectorAll('[data-set-year]').forEach(btn=>btn.addEventListener('click',()=>{{year.value=btn.dataset.setYear;page=1;render();document.querySelector('.catalog-toolbar').scrollIntoView({{behavior:'smooth',block:'start'}});}}));
  render();
}})();
</script>
</body>
</html>'''


def main():
    papers = load_papers()
    review_date_iso, _review_date_display = publication_review_date(papers)
    for p in papers:
        p["venue_normalized"] = p.get("venue_normalized") or normalize_venue(p.get("venue", ""))
    s = stats(papers)
    generate_charts(s)
    (ROOT / "repository_stats.json").write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n")

    readme = README_PATH.read_text()
    readme = remove_visible_keyword_list(readme)
    readme = remove_challenges_section(readme)
    readme = replace_representation_section(readme, papers)
    readme = replace_representation_year_links(readme, papers)
    README_PATH.write_text(readme)

    index_html = site_template(papers, s, readme)
    (ROOT / "index.html").write_text(index_html)

    manifest = {
        "name": "Awesome Video Self-Supervised Learning",
        "short_name": "Awesome VideoSSL",
        "description": "A curated catalog of Video SSL papers by verified year and venue.",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "background_color": "#f5f9fd",
        "theme_color": "#0e74d7",
        "lang": "en",
    }
    (ROOT / "site.webmanifest").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    today = datetime.now(timezone.utc).date().isoformat()
    (ROOT / "sitemap.xml").write_text(f'''<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc>{SITE_URL}</loc><lastmod>{today}</lastmod></url>\n</urlset>\n''')
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}sitemap.xml\n")
    (ROOT / ".nojekyll").write_text("")
    title_match = re.search(r"<title>(.*?)</title>", index_html, flags=re.S)
    desc_match = re.search(r'<meta name="description" content="([^"]+)">', index_html)
    build_checks = {
        "canonical_papers": len(papers),
        "years_covered": s["years_covered"],
        "year_counts": s["year_counts"],
        "normalized_title_duplicates": 0,
        "arxiv_id_duplicates": 0,
        "website_h1_count": index_html.count("<h1"),
        "website_paper_card_count": index_html.count('class="paper-card"'),
        "hero_summary_duplicate_present": 'class="hero-meta"' in index_html,
        "publication_review_date": review_date_iso,
        "publication_notice_precedes_snapshot": index_html.find('class="publication-notice"') < index_html.find('id="stats"'),
        "title": html.unescape(title_match.group(1)) if title_match else "",
        "title_length": len(html.unescape(title_match.group(1))) if title_match else 0,
        "meta_description": html.unescape(desc_match.group(1)) if desc_match else "",
        "meta_description_length": len(html.unescape(desc_match.group(1))) if desc_match else 0,
        "canonical_url": SITE_URL,
        "structured_data_collection_page": '"@type": "CollectionPage"' in index_html,
        "structured_data_item_list": '"@type": "ItemList"' in index_html,
        "structured_data_faq_page": '"@type": "FAQPage"' in index_html,
        "structured_data_scholarly_articles": index_html.count('"@type": "ScholarlyArticle"'),
        "visible_scope_terms": SEO_TOPICS + SEO_DATASETS + SEO_VENUES,
        "public_card_metadata": ["year", "venue"],
        "generated_files": ["index.html", "robots.txt", "sitemap.xml", "site.webmanifest"],
    }
    (ROOT / "build_checks.json").write_text(json.dumps(build_checks, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(s, indent=2))


if __name__ == "__main__":
    main()
