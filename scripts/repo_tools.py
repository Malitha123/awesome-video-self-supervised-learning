from __future__ import annotations

import html
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MEDIA_DIR = ROOT / "media"
README_PATH = ROOT / "README.md"
PAPERS_PATH = DATA_DIR / "papers.json"
CONFIG_PATH = DATA_DIR / "curation_config.json"

SITE_URL = "https://malitha123.github.io/awesome-video-self-supervised-learning/"
REPO_URL = "https://github.com/Malitha123/awesome-video-self-supervised-learning"

TARGET_BENCHMARKS = [
    "UCF101", "HMDB51", "Kinetics-400", "Something-Something V1",
    "Something-Something V2", "Diving48", "EPIC-KITCHENS", "FineGYM",
    "Charades", "Charades-Ego", "AVA", "Kinetics-600", "Kinetics-700",
    "Ego4D", "EGTEA", "Breakfast", "COIN", "Jester"
]

BENCHMARK_ALIASES = {
    "UCF101": ["ucf101", "ucf-101"],
    "HMDB51": ["hmdb51", "hmdb-51"],
    "Kinetics-400": ["kinetics-400", "kinetics 400", "k400"],
    "Kinetics-600": ["kinetics-600", "kinetics 600", "k600"],
    "Kinetics-700": ["kinetics-700", "kinetics 700", "k700"],
    "Something-Something V1": ["something-something v1", "something something v1", "ssv1", "ss-v1"],
    "Something-Something V2": ["something-something v2", "something something v2", "ssv2", "ss-v2"],
    "Diving48": ["diving48", "diving-48"],
    "EPIC-KITCHENS": ["epic-kitchens", "epic kitchens", "epic-kitchens-55", "epic-kitchens-100", "ek55", "ek100"],
    "FineGYM": ["finegym", "fine gym"],
    "Charades": ["charades"],
    "Charades-Ego": ["charades-ego", "charades ego"],
    "AVA": ["ava"],
    "Ego4D": ["ego4d"],
    "EGTEA": ["egtea"],
    "Breakfast": ["breakfast"],
    "COIN": ["coin"],
    "Jester": ["jester"],
}

FAMILY_ORDER = [
    "Contrastive",
    "Generative / Masked",
    "Pretext / Predictive",
    "Cross-Modal",
    "Other / Hybrid",
]


def normalize_title(title: str) -> str:
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    s = s.lower().replace("self supervised", "self-supervised")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def extract_arxiv_id(*values: str) -> str:
    for value in values:
        if not value:
            continue
        m = re.search(r"(?:arxiv[:./ ](?:abs/|pdf/)?)(\d{4}\.\d{4,5})(?:v\d+)?", value, flags=re.I)
        if not m:
            m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?", value, flags=re.I)
        if m:
            return m.group(1)
    return ""


def normalize_benchmarks(text_or_items: str | Iterable[str]) -> list[str]:
    if isinstance(text_or_items, str):
        raw = text_or_items
    else:
        raw = ", ".join(text_or_items)
    low = raw.lower()
    found = []
    for canonical, aliases in BENCHMARK_ALIASES.items():
        if any(re.search(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", low) for alias in aliases):
            found.append(canonical)
    return found


def normalize_venue(venue: str) -> str:
    x = venue.lower().strip()
    if "cvpr workshop" in x or "cvprw" in x:
        return "CVPR Workshops"
    if "cvpr" in x or "computer vision and pattern recognition" in x:
        return "CVPR"
    if "iccv workshop" in x or "iccvw" in x:
        return "ICCV Workshops"
    if "iccv" in x or "international conference on computer vision" in x:
        return "ICCV"
    if "eccv" in x or "european conference on computer vision" in x:
        return "ECCV"
    if "neurips" in x or "neural information processing systems" in x:
        return "NeurIPS"
    if "aaai" in x:
        return "AAAI"
    if "wacv" in x or "winter conference on applications of computer vision" in x:
        return "WACV"
    if "acm international conference on multimedia" in x:
        return "ACM MM"
    if "bmvc" in x or "british machine vision conference" in x:
        return "BMVC"
    if "icassp" in x:
        return "ICASSP"
    if "iclr" in x or "international conference on learning representation" in x:
        return "ICLR"
    if "transactions on pattern analysis and machine intelligence" in x or "tpami" in x:
        return "TPAMI"
    if "transactions on circuits and systems for video technology" in x or "tcsvt" in x:
        return "TCSVT"
    if "transactions on multimedia" in x:
        return "TMM"
    if "transactions on image processing" in x:
        return "TIP"
    if "pattern recognition letters" in x:
        return "Pattern Recognition Letters"
    if "pattern recognition" in x:
        return "Pattern Recognition"
    if "image and vision computing" in x:
        return "Image and Vision Computing"
    if "signal, image and video processing" in x:
        return "Signal, Image and Video Processing"
    if "engineering applications of artificial intelligence" in x or "eng. appl. artif. intell" in x:
        return "Engineering Applications of Artificial Intelligence"
    if "arxiv" in x or "preprint" in x or "techrxiv" in x:
        return "arXiv / Preprint"
    return venue.strip() or "Other"


def taxonomy_family_map(readme_text: str) -> dict[str, str]:
    family = None
    out: dict[str, str] = {}
    for raw in readme_text.splitlines():
        s = raw.strip()
        if s == "# Pretext Task":
            family = "Pretext / Predictive"
            continue
        if s == "# Contrastive Learning":
            family = "Contrastive"
            continue
        if s == "# Generative":
            family = "Generative / Masked"
            continue
        if s == "# Cross-Modal":
            family = "Cross-Modal"
            continue
        if s == "# Video SSL FAQ":
            family = None
            continue
        if family:
            m = re.match(r"-\s*\*\*(.*?)\*\*", s)
            if m:
                out[normalize_title(m.group(1))] = family
    return out


def infer_family(title: str, venue: str = "", taxonomy_map: dict[str, str] | None = None) -> str:
    norm = normalize_title(title)
    if taxonomy_map and norm in taxonomy_map:
        return taxonomy_map[norm]
    t = (title + " " + venue).lower()
    if any(k in t for k in ["audio-visual", "audio visual", "cross-modal", "cross modal", "multimodal", "omnimodal", "video-language", "language audio vision", "video and language", "video-text", "text-video"]):
        return "Cross-Modal"
    if any(k in t for k in ["masked", "masking", "mask ", "videomae", "video mae", "autoencoder", "autoregressive", "generative", "mim", "mvm"]):
        return "Generative / Masked"
    if any(k in t for k in ["contrast", "moco", "nce", "coclr", "tclr", "simclr", "non-contrastive"]):
        return "Contrastive"
    if any(k in t for k in ["predict", "prediction", "ranking", "rank ", "order", "rotation", "jigsaw", "playback", "speed", "temporal", "future", "incoherence", "continuity", "pretext", "shuffle"]):
        return "Pretext / Predictive"
    return "Other / Hybrid"


def parse_main_representation(readme_text: str) -> list[dict]:
    lines = readme_text.splitlines()
    taxonomy = taxonomy_family_map(readme_text)
    start = next(i for i, l in enumerate(lines) if l.strip().startswith("# Representation Learning"))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].strip() in {"# Challenges", "# Video SSL FAQ"}), len(lines))
    papers = []
    year_heading = None
    order = 0
    i = start + 1
    while i < end:
        s = lines[i].strip()
        ym = re.match(r"#\s*\*?(20\d{2}|201\d)\*?\s*$", s)
        if ym:
            year_heading = int(ym.group(1))
            i += 1
            continue
        m = re.match(r"-\s*\*\*(.*?)\*\*\s*(?:\(([^)]*)\))?\s*<br>\s*$", s)
        if not m:
            i += 1
            continue
        title = m.group(1).strip()
        date_label = (m.group(2) or "").strip()
        ymatch = re.search(r"(20\d{2}|201\d)", date_label)
        year = int(ymatch.group(1)) if ymatch else year_heading
        j = i + 1
        block = []
        while j < end:
            sj = lines[j].strip()
            if re.match(r"-\s*\*\*", sj) or re.match(r"#\s*\*?(20\d{2}|201\d)\*?\s*$", sj) or sj in {"# Challenges", "# Video SSL FAQ"}:
                break
            if sj:
                block.append(sj)
            j += 1
        venue = ""
        authors = ""
        benchmark_text = ""
        links: dict[str, str] = {}
        venue_idx = -1
        for bi, b in enumerate(block):
            vm = re.match(r"\*(.*?)\*\s*<br>\s*$", b)
            if vm:
                venue = vm.group(1).strip()
                venue_idx = bi
                break
        if venue_idx >= 0:
            for b in block[venue_idx + 1:]:
                if b.startswith("**Benchmarks:**"):
                    benchmark_text = b.replace("**Benchmarks:**", "", 1).replace("<br>", "").strip()
                    continue
                if b.startswith("**Datasets:**"):
                    benchmark_text = b.replace("**Datasets:**", "", 1).replace("<br>", "").strip()
                    continue
                for label, url in re.findall(r"\[\[([^\]]+)\]\]\(([^)]+)\)", b):
                    links[label.strip().lower().replace(" ", "_")] = url.strip()
                if "[[" in b:
                    continue
                if not authors and not b.startswith("<!--") and b != "-->":
                    authors = b.replace("<br>", "").strip()
        paper_url = links.get("paper", "")
        arxiv_id = extract_arxiv_id(paper_url, venue)
        paper = {
            "title": title,
            "normalized_title": normalize_title(title),
            "year": year,
            "date_label": date_label or str(year or ""),
            "venue": venue,
            "venue_normalized": normalize_venue(venue),
            "authors": [a.strip() for a in re.split(r"\s*(?:,|;|\band\b|&)\s*", authors) if a.strip()],
            "authors_display": authors,
            "benchmarks": normalize_benchmarks(benchmark_text),
            "benchmark_text": benchmark_text,
            "method_family": infer_family(title, venue, taxonomy),
            "paper_url": paper_url,
            "code_url": links.get("code", links.get("github", links.get("gitHub", ""))),
            "project_url": links.get("project_page", links.get("page", "")),
            "doi": "",
            "arxiv_id": arxiv_id,
            "source_order": order,
            "published_date": "",
            "added_at": "",
            "verification_urls": [],
            "discovery_source": "existing_repository",
        }
        papers.append(paper)
        order += 1
        i = j
    return papers


def load_papers() -> list[dict]:
    return json.loads(PAPERS_PATH.read_text())


def save_papers(papers: list[dict]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    PAPERS_PATH.write_text(json.dumps(papers, indent=2, ensure_ascii=False) + "\n")


def paper_links_markdown(p: dict) -> str:
    parts = []
    if p.get("paper_url"):
        parts.append(f"[[Paper]]({p['paper_url']})")
    if p.get("code_url"):
        parts.append(f"[[Code]]({p['code_url']})")
    if p.get("project_url"):
        parts.append(f"[[Project Page]]({p['project_url']})")
    return " ".join(parts)


def render_representation_section(papers: list[dict]) -> str:
    grouped: dict[int, list[dict]] = {}
    for p in papers:
        if p.get("year"):
            grouped.setdefault(int(p["year"]), []).append(p)
    chunks = ["# Representation Learning", ""]
    for year in sorted(grouped, reverse=True):
        chunks += [f"# *{year}*", ""]
        # Newly discovered papers have no source_order, keep them first by published date.
        def key(p: dict):
            is_existing = p.get("source_order") is not None
            if not is_existing:
                return (0, p.get("published_date", "9999-99-99"), p.get("normalized_title", ""))
            return (1, "", int(p.get("source_order", 10**9)))
        for p in sorted(grouped[year], key=key):
            label = p.get("date_label") or str(year)
            chunks.append(f"- **{p['title']}** ({label})<br>")
            chunks.append(f"*{p.get('venue') or 'arXiv preprint'}* <br>")
            authors_display = p.get("authors_display") or ", ".join(p.get("authors") or [])
            if authors_display:
                chunks.append(f"{authors_display}<br>")
            links = paper_links_markdown(p)
            if links:
                chunks.append(links)
            chunks.append("")
            chunks.append("")
    return "\n".join(chunks).rstrip() + "\n\n"


def replace_representation_section(readme_text: str, papers: list[dict]) -> str:
    pattern = re.compile(r"# Representation Learning\n.*?(?=\n# (?:Challenges|Video SSL FAQ)\n)", re.S)
    rendered = render_representation_section(papers).rstrip()
    return pattern.sub(rendered, readme_text, count=1)


def remove_challenges_section(readme_text: str) -> str:
    """Remove the old challenge/taxonomy appendix while preserving the FAQ."""
    readme_text = re.sub(r"\n# Challenges\n.*?(?=\n# Video SSL FAQ\n)", "\n", readme_text, flags=re.S)
    readme_text = re.sub(
        r"\n?<!-- - \[Challenges\]\(#Challenges\).*?-->\n?",
        "\n",
        readme_text,
        flags=re.S,
    )
    return readme_text


def stats(papers: list[dict]) -> dict:
    years = Counter(int(p["year"]) for p in papers if p.get("year"))
    venues = Counter(p.get("venue_normalized") or normalize_venue(p.get("venue", "")) for p in papers)
    benches = Counter()
    dataset_annotated = 0
    families = Counter()
    for p in papers:
        bs = p.get("datasets") or p.get("benchmarks") or []
        if bs:
            dataset_annotated += 1
            benches.update(bs)
        families[p.get("method_family") or "Other / Hybrid"] += 1
    top_venues = venues.most_common(12)
    other = sum(venues.values()) - sum(v for _, v in top_venues)
    if other:
        top_venues.append(("Other venues", other))
    family_rows = [(f, families.get(f, 0)) for f in FAMILY_ORDER if families.get(f, 0)]
    return {
        "papers_tracked": len(papers),
        "years_covered": f"{min(years)}–{max(years)}" if years else "",
        "year_counts": dict(sorted(years.items())),
        "venue_counts_top": top_venues,
        "dataset_counts_top": benches.most_common(10),
        "benchmark_counts_top": benches.most_common(10),
        "dataset_annotated_papers": dataset_annotated,
        "benchmark_annotated_papers": dataset_annotated,
        "family_counts": family_rows,
        "distinct_normalized_venues": len(venues),
    }


def replace_stats_section(readme_text: str, stats_md: str) -> str:
    # Remove legacy statistics block if present and replace with marked block.
    marked = f"<!-- AUTO:STATS:START -->\n{stats_md.rstrip()}\n<!-- AUTO:STATS:END -->\n\n"
    if "<!-- AUTO:STATS:START -->" in readme_text:
        return re.sub(r"<!-- AUTO:STATS:START -->.*?<!-- AUTO:STATS:END -->\n*", marked, readme_text, flags=re.S)
    legacy = re.compile(r"## Repository Statistics\n.*?(?=\n## Acknowledgments\n)", re.S)
    if legacy.search(readme_text):
        return legacy.sub(marked.rstrip(), readme_text, count=1)
    anchor = "\n## Acknowledgments\n"
    return readme_text.replace(anchor, "\n" + marked + "## Acknowledgments\n", 1)


def remove_visible_keyword_list(readme_text: str) -> str:
    return re.sub(
        r"\n?\*\*Common search terms covered by this resource:\*\*.*?(?=\n\n)",
        "",
        readme_text,
        flags=re.S,
    )


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
