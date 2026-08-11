#!/usr/bin/env python3
"""Build the complete 282-paper audit tables and verify required fields."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPERS_PATH = ROOT / "data" / "papers.json"
PROGRESS_PATH = ROOT / "data" / "audit_progress.json"
OUTPUT_DIR = ROOT / "data" / "audits"
VERIFIED_AS_OF = "2026-08-11"
EXPECTED_COUNT = 282


CSV_FIELDS = [
    "Title",
    "Authors",
    "Method",
    "Method family",
    "Pretraining datasets",
    "Evaluation datasets",
    "All datasets",
    "Year",
    "Venue",
    "Is NeurIPS",
    "Publication status",
    "DOI",
    "arXiv ID",
    "Paper URL",
    "Code URL",
    "Dataset notes",
    "Verified as of",
]


def join(values):
    return "; ".join(values or [])


def main():
    papers = json.loads(PAPERS_PATH.read_text())
    if len(papers) != EXPECTED_COUNT:
        raise SystemExit(f"Expected {EXPECTED_COUNT} papers, found {len(papers)}")

    normalized_titles = [paper["normalized_title"] for paper in papers]
    duplicates = sorted(title for title, count in Counter(normalized_titles).items() if count > 1)
    if duplicates:
        raise SystemExit(f"Duplicate canonical titles: {duplicates}")

    required = (
        "title", "method", "method_family", "pretraining_datasets", "evaluation_datasets",
        "year", "venue", "venue_normalized", "publication_status", "verification_urls",
    )
    errors = []
    for paper in papers:
        missing = [field for field in required if paper.get(field) in (None, "", [])]
        if paper.get("audit_status") != "verified":
            missing.append("audit_status=verified")
        if missing:
            errors.append(f"{paper.get('title', '<untitled>')}: {', '.join(missing)}")
    if errors:
        raise SystemExit("Incomplete paper records:\n" + "\n".join(errors))

    papers = sorted(papers, key=lambda paper: (-paper["year"], paper["title"].casefold()))
    csv_path = OUTPUT_DIR / "all_282_papers.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for paper in papers:
            writer.writerow({
                "Title": paper["title"],
                "Authors": paper.get("authors_display", join(paper.get("authors"))),
                "Method": paper["method"],
                "Method family": paper["method_family"],
                "Pretraining datasets": join(paper["pretraining_datasets"]),
                "Evaluation datasets": join(paper["evaluation_datasets"]),
                "All datasets": join(paper.get("datasets")),
                "Year": paper["year"],
                "Venue": paper["venue"],
                "Is NeurIPS": "Yes" if paper["venue_normalized"] == "NeurIPS" else "No",
                "Publication status": paper["publication_status"],
                "DOI": paper.get("doi", ""),
                "arXiv ID": paper.get("arxiv_id", ""),
                "Paper URL": paper.get("paper_url", ""),
                "Code URL": paper.get("code_url", ""),
                "Dataset notes": paper.get("dataset_notes", ""),
                "Verified as of": paper.get("audited_at", VERIFIED_AS_OF),
            })

    records = []
    for paper in papers:
        records.append({
            "title": paper["title"],
            "authors": paper.get("authors", []),
            "method": paper["method"],
            "method_family": paper["method_family"],
            "method_description": paper.get("method_description", ""),
            "pretraining_datasets": paper["pretraining_datasets"],
            "evaluation_datasets": paper["evaluation_datasets"],
            "all_datasets": paper.get("datasets", []),
            "dataset_notes": paper.get("dataset_notes", ""),
            "year": paper["year"],
            "venue": paper["venue"],
            "venue_normalized": paper["venue_normalized"],
            "is_neurips": paper["venue_normalized"] == "NeurIPS",
            "publication_status": paper["publication_status"],
            "doi": paper.get("doi", ""),
            "arxiv_id": paper.get("arxiv_id", ""),
            "paper_url": paper.get("paper_url", ""),
            "code_url": paper.get("code_url", ""),
            "project_url": paper.get("project_url", ""),
            "verification_urls": paper.get("verification_urls", []),
            "audit_notes": paper.get("audit_notes", ""),
            "verified_as_of": paper.get("audited_at", VERIFIED_AS_OF),
        })

    venue_counts = Counter(paper["venue_normalized"] for paper in papers)
    year_counts = Counter(paper["year"] for paper in papers)
    status_counts = Counter(paper["publication_status"] for paper in papers)
    payload = {
        "schema_version": 1,
        "title": "Canonical video self-supervised learning paper audit",
        "verified_as_of": VERIFIED_AS_OF,
        "canonical_paper_count": len(records),
        "sort_order": "year descending, title ascending",
        "source_policy": "Discover by exact-title scholarly search, then confirm using official proceedings, publisher or DOI metadata, arXiv, and official project records.",
        "dataset_policy": "Keep self-supervised or backbone pretraining datasets separate from downstream evaluation datasets.",
        "summary": {
            "peer_reviewed_count": status_counts["peer_reviewed"],
            "preprint_count": status_counts["preprint"],
            "neurips_count": venue_counts["NeurIPS"],
            "year_counts": {str(year): year_counts[year] for year in sorted(year_counts, reverse=True)},
            "venue_counts": dict(sorted(venue_counts.items(), key=lambda item: (-item[1], item[0]))),
        },
        "records": records,
    }
    json_path = OUTPUT_DIR / "all_282_papers.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    progress = json.loads(PROGRESS_PATH.read_text())
    progress["master_csv"] = "data/audits/all_282_papers.csv"
    progress["master_json"] = "data/audits/all_282_papers.json"
    progress["master_xlsx"] = "data/audits/all_282_papers.xlsx"
    progress["resume_instruction"] = "The 282-paper audit and master tables are complete. Future work should only re-verify time-sensitive preprint publication status or add newly curated papers."
    PROGRESS_PATH.write_text(json.dumps(progress, indent=2, ensure_ascii=False) + "\n")

    print(
        f"Wrote {len(records)} records to {csv_path.relative_to(ROOT)} and "
        f"{json_path.relative_to(ROOT)}; peer-reviewed={status_counts['peer_reviewed']}, "
        f"preprints={status_counts['preprint']}, NeurIPS={venue_counts['NeurIPS']}."
    )


if __name__ == "__main__":
    main()
