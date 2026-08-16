#!/usr/bin/env python3
"""Synchronize the hidden audit records with the canonical paper catalog.

The public README and website intentionally expose only a paper's year and
venue. This module keeps the richer method, dataset, publication, and evidence
metadata in ``data/`` aligned whenever the weekly curator adds or updates a
paper.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

from repo_tools import ROOT, normalize_title, normalize_venue


YEAR_CSV_FIELDS = [
    "Title",
    "Method",
    "Method family",
    "Pretraining datasets",
    "Evaluation datasets",
    "Year",
    "Venue",
    "Publication status",
    "DOI",
    "Verified as of",
]

MASTER_CSV_FIELDS = [
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

AUDIT_UPDATE_FIELDS = [
    "year",
    "date_label",
    "venue",
    "venue_normalized",
    "publication_status",
    "method",
    "method_family",
    "method_description",
    "pretraining_datasets",
    "evaluation_datasets",
    "datasets",
    "benchmarks",
    "benchmark_suites",
    "benchmark_text",
    "dataset_notes",
    "paper_url",
    "code_url",
    "project_url",
    "doi",
    "arxiv_id",
    "published_date",
    "verification_urls",
    "venue_evidence",
    "audit_notes",
    "previous_titles",
    "publication_history",
    "audit_status",
    "audit_year",
    "audited_at",
    "discovery_source",
]

REQUIRED_FIELDS = [
    "title",
    "normalized_title",
    "method",
    "method_family",
    "pretraining_datasets",
    "evaluation_datasets",
    "datasets",
    "year",
    "venue",
    "venue_normalized",
    "publication_status",
    "verification_urls",
    "venue_evidence",
    "audit_status",
    "audit_year",
    "audited_at",
]


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def joined(values: list[str] | None) -> str:
    return "; ".join(values or [])


def current_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def latest_verification_date(papers: list[dict], fallback: str) -> str:
    dates = [str(paper.get("audited_at", "")) for paper in papers]
    valid = [value for value in dates if len(value) == 10 and value[4] == "-" and value[7] == "-"]
    return max(valid, default=fallback)


def validate_and_normalize(papers: list[dict]) -> None:
    errors: list[str] = []
    seen_titles: dict[str, str] = {}
    seen_arxiv: dict[str, str] = {}

    for paper in papers:
        title = " ".join(str(paper.get("title", "")).split())
        paper["title"] = title
        normalized = normalize_title(title)
        paper["normalized_title"] = normalized
        paper["venue_normalized"] = paper.get("venue_normalized") or normalize_venue(paper.get("venue", ""))
        paper["datasets"] = unique(
            list(paper.get("datasets") or [])
            or ((paper.get("pretraining_datasets") or []) + (paper.get("evaluation_datasets") or []))
        )
        paper["audit_year"] = int(paper.get("year") or 0)

        if normalized in seen_titles:
            errors.append(f"duplicate normalized title: {title} / {seen_titles[normalized]}")
        else:
            seen_titles[normalized] = title

        arxiv_id = str(paper.get("arxiv_id", "")).strip()
        if arxiv_id:
            if arxiv_id in seen_arxiv:
                errors.append(f"duplicate arXiv ID {arxiv_id}: {title} / {seen_arxiv[arxiv_id]}")
            else:
                seen_arxiv[arxiv_id] = title

        missing = [field for field in REQUIRED_FIELDS if paper.get(field) in (None, "", [])]
        if paper.get("audit_status") != "verified":
            missing.append("audit_status=verified")
        if paper.get("publication_status") not in {"peer_reviewed", "preprint"}:
            missing.append("valid publication_status")
        if paper.get("audit_year") != paper.get("year"):
            missing.append("audit_year=current year")
        if missing:
            errors.append(f"{title or '<untitled>'}: missing {', '.join(unique(missing))}")

    if errors:
        raise ValueError("Cannot synchronize incomplete audit data:\n" + "\n".join(errors))


def audit_updates(paper: dict) -> dict:
    return {field: paper[field] for field in AUDIT_UPDATE_FIELDS if field in paper}


def year_status(year: int, papers: list[dict], fallback_date: str) -> dict:
    return {
        "status": "complete",
        "paper_count": len(papers),
        "peer_reviewed_count": sum(paper["publication_status"] == "peer_reviewed" for paper in papers),
        "preprint_count": sum(paper["publication_status"] == "preprint" for paper in papers),
        "audit_file": f"data/audits/{year}.json",
        "summary_file": f"data/audits/{year}.csv",
        "verified_as_of": latest_verification_date(papers, fallback_date),
    }


def write_year_files(audits_dir: Path, year: int, papers: list[dict], fallback_date: str) -> None:
    verified_as_of = latest_verification_date(papers, fallback_date)
    payload = {
        "schema_version": 2,
        "year": year,
        "status": "complete",
        "verified_as_of": verified_as_of,
        "paper_count": len(papers),
        "source_policy": (
            "Use exact-title scholarly discovery, then verify venue and metadata against an official "
            "conference, publisher, DOI, or preprint record. Do not promote a search-result venue "
            "without primary-source confirmation."
        ),
        "dataset_policy": (
            "Record separately the datasets used for self-supervised or backbone pretraining and "
            "the datasets used for downstream evaluation."
        ),
        "records": [
            {"normalized_title": paper["normalized_title"], "updates": audit_updates(paper)}
            for paper in papers
        ],
    }
    (audits_dir / f"{year}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    with (audits_dir / f"{year}.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=YEAR_CSV_FIELDS)
        writer.writeheader()
        for paper in papers:
            writer.writerow({
                "Title": paper["title"],
                "Method": paper["method"],
                "Method family": paper["method_family"],
                "Pretraining datasets": joined(paper["pretraining_datasets"]),
                "Evaluation datasets": joined(paper["evaluation_datasets"]),
                "Year": paper["year"],
                "Venue": paper["venue"],
                "Publication status": paper["publication_status"],
                "DOI": paper.get("doi", ""),
                "Verified as of": paper["audited_at"],
            })


def master_row(paper: dict) -> dict:
    return {
        "Title": paper["title"],
        "Authors": paper.get("authors_display") or joined(paper.get("authors")),
        "Method": paper["method"],
        "Method family": paper["method_family"],
        "Pretraining datasets": joined(paper["pretraining_datasets"]),
        "Evaluation datasets": joined(paper["evaluation_datasets"]),
        "All datasets": joined(paper["datasets"]),
        "Year": paper["year"],
        "Venue": paper["venue"],
        "Is NeurIPS": "Yes" if paper["venue_normalized"] == "NeurIPS" else "No",
        "Publication status": paper["publication_status"],
        "DOI": paper.get("doi", ""),
        "arXiv ID": paper.get("arxiv_id", ""),
        "Paper URL": paper.get("paper_url", ""),
        "Code URL": paper.get("code_url", ""),
        "Dataset notes": paper.get("dataset_notes", ""),
        "Verified as of": paper["audited_at"],
    }


def master_record(paper: dict) -> dict:
    return {
        "title": paper["title"],
        "authors": paper.get("authors", []),
        "method": paper["method"],
        "method_family": paper["method_family"],
        "method_description": paper.get("method_description", ""),
        "pretraining_datasets": paper["pretraining_datasets"],
        "evaluation_datasets": paper["evaluation_datasets"],
        "all_datasets": paper["datasets"],
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
        "verification_urls": paper["verification_urls"],
        "venue_evidence": paper.get("venue_evidence", ""),
        "audit_notes": paper.get("audit_notes", ""),
        "publication_history": paper.get("publication_history", []),
        "verified_as_of": paper["audited_at"],
    }


def write_master_files(audits_dir: Path, papers: list[dict], fallback_date: str) -> dict[str, str]:
    sorted_papers = sorted(papers, key=lambda paper: (-int(paper["year"]), paper["title"].casefold()))
    rows = [master_row(paper) for paper in sorted_papers]
    verified_as_of = latest_verification_date(papers, fallback_date)
    csv_path = audits_dir / "all_canonical_papers.csv"
    json_path = audits_dir / "all_canonical_papers.json"
    xlsx_path = audits_dir / "all_canonical_papers.xlsx"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MASTER_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    venue_counts = Counter(paper["venue_normalized"] for paper in papers)
    year_counts = Counter(int(paper["year"]) for paper in papers)
    status_counts = Counter(paper["publication_status"] for paper in papers)
    payload = {
        "schema_version": 2,
        "title": "Current canonical video self-supervised learning paper audit",
        "verified_as_of": verified_as_of,
        "canonical_paper_count": len(papers),
        "sort_order": "year descending, title ascending",
        "source_policy": (
            "Discover through scholarly indexes, then confirm using official proceedings, publisher "
            "or DOI metadata, arXiv, and official project records."
        ),
        "dataset_policy": (
            "Keep self-supervised or backbone pretraining datasets separate from downstream "
            "evaluation datasets."
        ),
        "summary": {
            "peer_reviewed_count": status_counts["peer_reviewed"],
            "preprint_count": status_counts["preprint"],
            "neurips_count": venue_counts["NeurIPS"],
            "year_counts": {str(year): year_counts[year] for year in sorted(year_counts, reverse=True)},
            "venue_counts": dict(sorted(venue_counts.items(), key=lambda item: (-item[1], item[0]))),
        },
        "records": [master_record(paper) for paper in sorted_papers],
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Canonical papers"
    sheet.append(MASTER_CSV_FIELDS)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in rows:
        sheet.append([row[field] for field in MASTER_CSV_FIELDS])
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    widths = {
        "A": 65, "B": 45, "C": 32, "D": 24, "E": 38, "F": 42, "G": 48,
        "H": 10, "I": 42, "J": 12, "K": 18, "L": 28, "M": 16, "N": 55,
        "O": 45, "P": 70, "Q": 16,
    }
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width
    workbook.save(xlsx_path)

    return {
        "master_csv": "data/audits/all_canonical_papers.csv",
        "master_json": "data/audits/all_canonical_papers.json",
        "master_xlsx": "data/audits/all_canonical_papers.xlsx",
    }


def sync_catalog(root: Path = ROOT, verified_as_of: str | None = None) -> dict:
    snapshot_date = verified_as_of or current_date()
    papers_path = root / "data" / "papers.json"
    progress_path = root / "data" / "audit_progress.json"
    audits_dir = root / "data" / "audits"
    audits_dir.mkdir(parents=True, exist_ok=True)

    papers = json.loads(papers_path.read_text(encoding="utf-8"))
    validate_and_normalize(papers)
    papers_path.write_text(json.dumps(papers, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    grouped: dict[int, list[dict]] = {}
    for paper in papers:
        grouped.setdefault(int(paper["year"]), []).append(paper)
    years = sorted(grouped, reverse=True)
    for year in years:
        write_year_files(audits_dir, year, grouped[year], snapshot_date)

    master_paths = write_master_files(audits_dir, papers, snapshot_date)
    progress = json.loads(progress_path.read_text(encoding="utf-8")) if progress_path.exists() else {}
    if "historical_snapshot" not in progress and progress.get("master_json", "").endswith("all_282_papers.json"):
        progress["historical_snapshot"] = {
            "canonical_paper_count": 282,
            "verified_as_of": "2026-08-11",
            "csv": progress.get("master_csv"),
            "json": progress.get("master_json"),
            "xlsx": progress.get("master_xlsx"),
        }

    latest_date = latest_verification_date(papers, snapshot_date)
    progress.update({
        "schema_version": 2,
        "catalog_file": "data/papers.json",
        "canonical_paper_count": len(papers),
        "last_checkpoint_at": latest_date,
        "processing_order": "descending_year",
        "completed_years": years,
        "next_year": None,
        "verified_paper_count": len(papers),
        "remaining_paper_count": 0,
        "year_status": {str(year): year_status(year, grouped[year], snapshot_date) for year in years},
        "resume_instruction": (
            "The current catalog is fully synchronized. Re-verify time-sensitive preprints, review "
            "new candidates, then rebuild and validate after every accepted change."
        ),
        **master_paths,
    })
    progress_path.write_text(json.dumps(progress, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "paper_count": len(papers),
        "years": years,
        "verified_as_of": latest_date,
        **master_paths,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verified-as-of",
        help="ISO date for this synchronization checkpoint. Defaults to the current UTC date.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = sync_catalog(verified_as_of=args.verified_as_of)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
