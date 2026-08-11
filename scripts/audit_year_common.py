#!/usr/bin/env python3
"""Shared helpers for descending-year catalog audit checkpoints."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


VERIFIED_AS_OF = "2026-08-11"


def unique(items):
    return list(dict.fromkeys(item for item in items if item))


def split(value):
    return [item.strip() for item in value.split(";") if item.strip()]


def normalize_title(value):
    return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())


def spec(method, family, description, pretraining, evaluation, venue, venue_normalized,
         *, year, status="peer_reviewed", url="", doi="", arxiv="", notes="", new_title=""):
    return {
        "method": method, "method_family": family, "method_description": description,
        "pretraining_datasets": split(pretraining), "evaluation_datasets": split(evaluation),
        "dataset_notes": notes, "venue": venue, "venue_normalized": venue_normalized,
        "year": year, "publication_status": status, "paper_url": url, "doi": doi,
        "arxiv_id": arxiv, "new_title": new_title,
    }


AUDIT_UPDATE_FIELDS = [
    "year", "date_label", "venue", "venue_normalized", "publication_status", "method",
    "method_family", "method_description", "pretraining_datasets", "evaluation_datasets",
    "datasets", "benchmarks", "benchmark_suites", "benchmark_text", "dataset_notes",
    "paper_url", "code_url", "project_url", "doi", "arxiv_id", "published_date",
    "verification_urls", "venue_evidence", "audit_notes", "previous_titles",
]


def audit_updates(paper):
    return {key: paper[key] for key in AUDIT_UPDATE_FIELDS if key in paper}


def write_audit(root, year, papers):
    audits_dir = root / "data" / "audits"
    records = [{"normalized_title": p["normalized_title"], "updates": audit_updates(p)} for p in papers]
    payload = {
        "schema_version": 1, "year": year, "status": "complete", "verified_as_of": VERIFIED_AS_OF,
        "paper_count": len(records),
        "source_policy": "Use exact-title scholarly discovery, then verify venue and metadata against an official conference, publisher, DOI, or preprint record. Do not promote a search-result venue without primary-source confirmation.",
        "dataset_policy": "Record separately the datasets used for self-supervised or backbone pretraining and the datasets used for downstream evaluation. Preserve named benchmark suites and explicitly label unnamed private collections.",
        "records": records,
    }
    (audits_dir / f"{year}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    fields = ["Title", "Method", "Method family", "Pretraining datasets", "Evaluation datasets", "Year", "Venue", "Publication status", "DOI", "Verified as of"]
    with (audits_dir / f"{year}.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for paper in papers:
            writer.writerow({
                "Title": paper["title"], "Method": paper["method"], "Method family": paper["method_family"],
                "Pretraining datasets": "; ".join(paper["pretraining_datasets"]),
                "Evaluation datasets": "; ".join(paper["evaluation_datasets"]),
                "Year": paper["year"], "Venue": paper["venue"], "Publication status": paper["publication_status"],
                "DOI": paper.get("doi", ""), "Verified as of": VERIFIED_AS_OF,
            })


def status_block(year, papers):
    return {
        "status": "complete", "paper_count": len(papers),
        "peer_reviewed_count": sum(p["publication_status"] == "peer_reviewed" for p in papers),
        "preprint_count": sum(p["publication_status"] == "preprint" for p in papers),
        "audit_file": f"data/audits/{year}.json", "summary_file": f"data/audits/{year}.csv",
        "verified_as_of": VERIFIED_AS_OF,
    }


def apply_spec(paper, data, original_year):
    old_title = paper["title"]
    new_title = data.get("new_title") or old_title
    if new_title != old_title:
        paper["previous_titles"] = unique(paper.get("previous_titles", []) + [old_title])
        paper["title"] = new_title
        paper["normalized_title"] = normalize_title(new_title)
    for field in ("method", "method_family", "method_description", "pretraining_datasets", "evaluation_datasets", "dataset_notes", "venue", "venue_normalized", "year", "publication_status"):
        paper[field] = data[field]
    paper["date_label"] = str(data["year"])
    paper["published_date"] = str(data["year"])
    paper["datasets"] = unique(data["pretraining_datasets"] + data["evaluation_datasets"])
    paper["benchmarks"] = data["evaluation_datasets"]
    paper["benchmark_text"] = ", ".join(data["evaluation_datasets"])
    if data.get("paper_url"):
        paper["paper_url"] = data["paper_url"]
    paper["doi"] = data.get("doi", "")
    paper["arxiv_id"] = data.get("arxiv_id", "") or paper.get("arxiv_id", "")
    if not paper["arxiv_id"]:
        match = re.search(r"(?:abs/|pdf/|arXiv:)(\d{4}\.\d{4,5})", paper.get("paper_url", "") + " " + paper.get("venue", ""), re.I)
        paper["arxiv_id"] = match.group(1) if match else ""
    verification = [paper.get("paper_url", "")]
    if paper["doi"]:
        verification.append("https://doi.org/" + paper["doi"])
    if paper["arxiv_id"]:
        verification.append("https://arxiv.org/abs/" + paper["arxiv_id"])
    paper["verification_urls"] = unique(verification)
    paper["venue_evidence"] = "arxiv_record_and_exact_title_publication_search" if data["publication_status"] == "preprint" else "official_proceedings_or_publisher_record"
    if data["publication_status"] == "preprint":
        paper["audit_notes"] = "Exact-title and author-record searches found no peer-reviewed version through the verification date."
    elif data["year"] != original_year:
        paper["audit_notes"] = f"The initial {original_year} record was reconciled to the accepted archival publication version."
    else:
        paper.pop("audit_notes", None)
    paper["audited_at"] = VERIFIED_AS_OF
    paper["discovery_source"] = "exact_title_scholarly_search_then_primary_source"


def finalize_year(root, original_year, specs, completed_years, next_year):
    papers_path = root / "data" / "papers.json"
    papers = json.loads(papers_path.read_text())
    initial = [paper for paper in papers if paper.get("year") == original_year]
    initial_titles = {paper["title"] for paper in initial}
    if initial_titles != set(specs):
        raise SystemExit(
            f"{original_year} mapping mismatch: "
            f"missing={sorted(initial_titles-set(specs))}, extra={sorted(set(specs)-initial_titles)}"
        )
    for paper in initial:
        apply_spec(paper, specs[paper["title"]], original_year)

    completed = {}
    for year in completed_years:
        year_papers = [paper for paper in papers if paper.get("year") == year]
        for paper in year_papers:
            paper["audit_status"] = "verified"
            paper["audit_year"] = year
            paper["audited_at"] = VERIFIED_AS_OF
        completed[year] = year_papers
    papers_path.write_text(json.dumps(papers, indent=2, ensure_ascii=False) + "\n")
    for year in completed_years:
        write_audit(root, year, completed[year])

    verified = sum(len(completed[year]) for year in completed_years)
    progress_path = root / "data" / "audit_progress.json"
    progress = json.loads(progress_path.read_text())
    if next_year is None:
        resume_instruction = "All canonical paper years are complete. Rebuild the site, validate the catalog, and generate the final all-paper audit tables and archive."
    else:
        resume_instruction = f"Start with {next_year}. Verify exact-title publication history, fill method and split pretraining/evaluation datasets, rebuild the site, validate the catalog, and save the {next_year} checkpoint."
    progress.update({
        "last_checkpoint_at": VERIFIED_AS_OF, "completed_years": list(completed_years), "next_year": next_year,
        "verified_paper_count": verified, "remaining_paper_count": len(papers) - verified,
        "resume_instruction": resume_instruction,
    })
    progress["year_status"] = {str(year): status_block(year, completed[year]) for year in completed_years}
    progress_path.write_text(json.dumps(progress, indent=2, ensure_ascii=False) + "\n")
    print(
        f"Finalized original {original_year} cohort and reconciled completed years: "
        + ", ".join(f"{year}={len(completed[year])}" for year in completed_years)
    )
