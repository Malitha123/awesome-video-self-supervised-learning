#!/usr/bin/env python3
"""Apply one completed, reviewable year audit to the canonical paper catalog."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from repo_tools import DATA_DIR, PAPERS_PATH, normalize_title, save_papers


REQUIRED_UPDATE_FIELDS = {
    "year",
    "venue",
    "venue_normalized",
    "publication_status",
    "method",
    "method_family",
    "pretraining_datasets",
    "evaluation_datasets",
    "datasets",
    "verification_urls",
    "venue_evidence",
}


def load_json(path: Path) -> object:
    return json.loads(path.read_text())


def main() -> None:
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        raise SystemExit("Usage: python scripts/apply_year_audit.py YEAR")

    year = int(sys.argv[1])
    audit_path = DATA_DIR / "audits" / f"{year}.json"
    if not audit_path.exists():
        raise SystemExit(f"Audit file not found: {audit_path.relative_to(DATA_DIR.parent)}")

    audit = load_json(audit_path)
    if not isinstance(audit, dict):
        raise SystemExit("Audit file must contain a JSON object")
    if audit.get("year") != year or audit.get("status") != "complete":
        raise SystemExit("Audit year must match and status must be complete")

    records = audit.get("records")
    if not isinstance(records, list) or len(records) != audit.get("paper_count"):
        raise SystemExit("Audit record count does not match paper_count")

    papers = load_json(PAPERS_PATH)
    if not isinstance(papers, list):
        raise SystemExit("data/papers.json must contain a JSON array")

    papers_for_year = [p for p in papers if p.get("year") == year]
    if len(papers_for_year) != audit.get("paper_count"):
        raise SystemExit(
            f"Catalog has {len(papers_for_year)} papers for {year}, "
            f"but audit declares {audit.get('paper_count')}"
        )

    by_title = {p.get("normalized_title") or normalize_title(p["title"]): p for p in papers}
    seen: set[str] = set()
    for record in records:
        normalized_title = record.get("normalized_title", "")
        updates = record.get("updates")
        if normalized_title in seen:
            raise SystemExit(f"Duplicate audit title: {normalized_title}")
        seen.add(normalized_title)
        if normalized_title not in by_title:
            raise SystemExit(f"Audit title not found in catalog: {normalized_title}")
        if not isinstance(updates, dict):
            raise SystemExit(f"Missing updates object for: {normalized_title}")
        missing = sorted(REQUIRED_UPDATE_FIELDS - updates.keys())
        if missing:
            raise SystemExit(f"Missing required fields for {normalized_title}: {', '.join(missing)}")
        if updates["year"] != year:
            raise SystemExit(f"Year mismatch for: {normalized_title}")
        if not updates["verification_urls"]:
            raise SystemExit(f"No verification URLs for: {normalized_title}")

        paper = by_title[normalized_title]
        paper.update(updates)
        paper["normalized_title"] = normalize_title(paper["title"])
        paper["audit_status"] = "verified"
        paper["audit_year"] = year
        paper["audited_at"] = audit["verified_as_of"]
        paper["discovery_source"] = "exact_title_scholarly_search_then_primary_source"

    expected_titles = {
        p.get("normalized_title") or normalize_title(p["title"]) for p in papers_for_year
    }
    if seen != expected_titles:
        missing = sorted(expected_titles - seen)
        extra = sorted(seen - expected_titles)
        raise SystemExit(f"Audit/catalog title mismatch; missing={missing}, extra={extra}")

    save_papers(papers)
    print(f"Applied complete {year} audit to {len(records)} canonical papers.")


if __name__ == "__main__":
    main()
