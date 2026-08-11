#!/usr/bin/env python3
"""Point peer-reviewed records at official proceedings or publisher pages."""

from __future__ import annotations

import json
from pathlib import Path

from audit_year_common import unique, write_audit


ROOT = Path(__file__).resolve().parents[1]
PAPERS_PATH = ROOT / "data" / "papers.json"


UPDATES = {
    "Self-supervised learning of video representations from a child's perspective": {
        "paper_url": "https://escholarship.org/uc/item/5ng8w8tv",
    },
    "Self-Supervised Learning via Multi-Transformation Classification for Action Recognition": {
        "paper_url": "https://doi.org/10.1109/ICMEW63481.2024.10645477",
    },
    "Exploring Relations in Untrimmed Videos for Self-Supervised Learning": {
        "paper_url": "https://dl.acm.org/doi/10.1145/3473342",
        "doi": "10.1145/3473342",
    },
    "Contrastive spatio-temporal pretext learning for self-supervised video representation": {
        "paper_url": "https://ojs.aaai.org/index.php/AAAI/article/view/20248",
        "doi": "10.1609/aaai.v36i3.20248",
    },
    "Self-Supervised Video Representation Learning with Motion-Contrastive Perception": {
        "paper_url": "https://ieeexplore.ieee.org/document/9859802/",
        "doi": "10.1109/ICME52920.2022.9859802",
    },
    "Self-supervised spatiotemporal representation learning by exploiting video continuity": {
        "paper_url": "https://ojs.aaai.org/index.php/AAAI/article/view/20047",
        "doi": "10.1609/aaai.v36i2.20047",
    },
    "Static and Dynamic Concepts for Self-supervised Video Representation Learning": {
        "paper_url": "https://link.springer.com/chapter/10.1007/978-3-031-19809-0_9",
        "doi": "10.1007/978-3-031-19809-0_9",
    },
    "SOS! Self-supervised Learning over Sets of Handled Objects in Egocentric Action Recognition": {
        "paper_url": "https://link.springer.com/chapter/10.1007/978-3-031-19778-9_35",
        "doi": "10.1007/978-3-031-19778-9_35",
    },
    "LAVA: Language Audio Vision Alignment for Data-Efficient Video Pre-Training": {
        "paper_url": "https://openreview.net/forum?id=uwcwviTrLY3",
    },
}


def main():
    papers = json.loads(PAPERS_PATH.read_text())
    by_title = {paper["title"]: paper for paper in papers}
    missing = sorted(set(UPDATES) - set(by_title))
    if missing:
        raise SystemExit(f"Missing titles: {missing}")

    for title, update in UPDATES.items():
        paper = by_title[title]
        old_url = paper.get("paper_url", "")
        paper["paper_url"] = update["paper_url"]
        if update.get("doi"):
            paper["doi"] = update["doi"]
        verification = [paper["paper_url"]]
        if paper.get("doi"):
            verification.append("https://doi.org/" + paper["doi"])
        if paper.get("arxiv_id"):
            verification.append("https://arxiv.org/abs/" + paper["arxiv_id"])
        verification.extend(paper.get("verification_urls", []))
        paper["verification_urls"] = unique(verification)
        note = "The main catalog link now points to the official proceedings or publisher record; the arXiv version remains in verification metadata."
        existing = (paper.get("audit_notes") or "").strip()
        if note not in existing:
            paper["audit_notes"] = (existing + " " + note).strip()
        if old_url and old_url != paper["paper_url"]:
            paper["previous_paper_urls"] = unique(paper.get("previous_paper_urls", []) + [old_url])

    PAPERS_PATH.write_text(json.dumps(papers, indent=2, ensure_ascii=False) + "\n")
    for year in (2024, 2022):
        write_audit(ROOT, year, [paper for paper in papers if paper["year"] == year])
    print(f"Updated {len(UPDATES)} peer-reviewed records to official publication URLs.")


if __name__ == "__main__":
    main()
