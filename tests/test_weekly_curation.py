from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from curate_weekly import (  # noqa: E402
    apply_verified_update,
    find_existing_match,
    paper_validation_errors,
    publication_candidate_needs_review,
    verdict_to_paper,
)
from sync_catalog_audits import sync_catalog  # noqa: E402
from repo_tools import replace_representation_year_links  # noqa: E402


def preprint_record() -> dict:
    return {
        "title": "Example Self-Supervised Video Model",
        "normalized_title": "example self supervised video model",
        "year": 2025,
        "date_label": "2025",
        "venue": "arXiv preprint",
        "venue_normalized": "arXiv / Preprint",
        "publication_status": "preprint",
        "authors": ["A. Researcher"],
        "authors_display": "A. Researcher",
        "benchmarks": ["UCF101"],
        "benchmark_text": "UCF101",
        "method": "Example Method",
        "method_family": "Contrastive",
        "method_description": "A contrastive video representation method.",
        "pretraining_datasets": ["Kinetics-400"],
        "evaluation_datasets": ["UCF101"],
        "datasets": ["Kinetics-400", "UCF101"],
        "dataset_notes": "Pretrained on Kinetics-400 and evaluated on UCF101.",
        "paper_url": "https://arxiv.org/abs/2501.01234",
        "code_url": "",
        "project_url": "",
        "doi": "",
        "arxiv_id": "2501.01234",
        "source_order": None,
        "published_date": "2025-01-03",
        "added_at": "2025-01-03T00:00:00+00:00",
        "verification_urls": ["https://arxiv.org/abs/2501.01234"],
        "venue_evidence": "arXiv record",
        "audit_notes": "No archival publication was confirmed.",
        "audit_status": "verified",
        "audit_year": 2025,
        "audited_at": "2025-01-03",
        "discovery_source": "arXiv",
    }


def conference_candidate() -> dict:
    return {
        "title": "Example Self-Supervised Video Model",
        "abstract": "A self-supervised video representation method evaluated on UCF101.",
        "authors": ["A. Researcher"],
        "published_date": "2026-06-01",
        "year": 2026,
        "paper_url": "https://openaccess.thecvf.com/example",
        "arxiv_id": "2501.01234",
        "doi": "10.1000/example",
        "venue_hint": "CVPR",
        "source_type": "proceedings-article",
        "discovery_source": "OpenAlex",
    }


def conference_verdict() -> dict:
    return {
        "candidate_key": "2501.01234",
        "action": "update",
        "reason": "Official proceedings confirm the archival version.",
        "existing_normalized_title": "example self supervised video model",
        "canonical_title": "Example Self-Supervised Video Model",
        "year": 2026,
        "venue": "CVPR 2026",
        "venue_normalized": "CVPR",
        "publication_status": "peer_reviewed",
        "authors": ["A. Researcher"],
        "benchmarks": ["UCF101"],
        "method_family": "Contrastive",
        "method": "Example Method",
        "method_description": "A contrastive video representation method.",
        "pretraining_datasets": ["Kinetics-400"],
        "evaluation_datasets": ["UCF101"],
        "dataset_notes": "Pretrained on Kinetics-400 and evaluated on UCF101.",
        "paper_url": "https://openaccess.thecvf.com/example",
        "code_url": "",
        "project_url": "",
        "arxiv_id": "2501.01234",
        "doi": "10.1000/example",
        "evidence_urls": ["https://openaccess.thecvf.com/example"],
        "venue_evidence": "Official CVF proceedings",
        "audit_notes": "The original arXiv manuscript was published at CVPR 2026.",
    }


class WeeklyCurationTests(unittest.TestCase):
    def test_publication_upgrade_is_reviewed_and_updates_one_record(self):
        original = preprint_record()
        candidate = conference_candidate()
        matched, reason, score = find_existing_match(candidate, [original])
        self.assertIs(matched, original)
        self.assertEqual(reason, "arXiv ID")
        self.assertEqual(score, 1.0)
        self.assertTrue(publication_candidate_needs_review(candidate, original))

        changed = apply_verified_update(original, candidate, conference_verdict())
        self.assertIn("venue", changed)
        self.assertEqual(original["venue"], "CVPR 2026")
        self.assertEqual(original["publication_status"], "peer_reviewed")
        self.assertEqual(original["arxiv_id"], "2501.01234")
        self.assertEqual(len(original["publication_history"]), 1)
        self.assertEqual(original["publication_history"][0]["venue_normalized"], "arXiv / Preprint")
        self.assertEqual(paper_validation_errors(original), [])

    def test_unchanged_duplicate_does_not_consume_ai_review(self):
        original = preprint_record()
        unchanged = {
            **conference_candidate(),
            "discovery_source": "arXiv",
            "paper_url": original["paper_url"],
            "doi": "",
            "year": original["year"],
        }
        self.assertFalse(publication_candidate_needs_review(unchanged, original))

    def test_complete_new_paper_passes_hidden_metadata_validation(self):
        verdict = conference_verdict()
        verdict.update({
            "action": "add",
            "existing_normalized_title": "",
            "canonical_title": "A New Video SSL Paper",
            "arxiv_id": "2601.05678",
        })
        candidate = {
            **conference_candidate(),
            "title": "A New Video SSL Paper",
            "arxiv_id": "2601.05678",
        }
        paper = verdict_to_paper(candidate, verdict)
        self.assertEqual(paper_validation_errors(paper), [])
        self.assertEqual(paper["audit_status"], "verified")
        self.assertEqual(paper["audit_year"], 2026)

    def test_peer_reviewed_record_cannot_be_downgraded(self):
        record = preprint_record()
        apply_verified_update(record, conference_candidate(), conference_verdict())
        downgrade = conference_verdict()
        downgrade.update({
            "venue": "arXiv preprint",
            "publication_status": "preprint",
            "paper_url": "https://arxiv.org/abs/2501.01234",
            "doi": "",
        })
        with self.assertRaisesRegex(ValueError, "refusing to downgrade"):
            apply_verified_update(record, conference_candidate(), downgrade)

    def test_dynamic_audit_sync_accepts_catalog_growth(self):
        record = preprint_record()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data" / "audits").mkdir(parents=True)
            (root / "data" / "papers.json").write_text(json.dumps([record]), encoding="utf-8")
            (root / "data" / "audit_progress.json").write_text(
                json.dumps({"schema_version": 1, "canonical_paper_count": 0}), encoding="utf-8"
            )
            result = sync_catalog(root, verified_as_of="2026-08-17")
            progress = json.loads((root / "data" / "audit_progress.json").read_text())
            master = json.loads((root / "data" / "audits" / "all_canonical_papers.json").read_text())
            self.assertEqual(result["paper_count"], 1)
            self.assertEqual(progress["canonical_paper_count"], 1)
            self.assertEqual(master["canonical_paper_count"], 1)
            self.assertTrue((root / "data" / "audits" / "all_canonical_papers.xlsx").is_file())

    def test_readme_year_links_follow_catalog_years(self):
        readme = (
            "- [Representation Learning](#Representation-Learning)\n"
            "   - [2026](#2026)\n"
            "   - [2025](#2025)\n"
            "- [Surveys](#Surveys)\n"
        )
        updated = replace_representation_year_links(readme, [{"year": 2027}, {"year": 2026}])
        self.assertIn("   - [2027](#2027)", updated)
        self.assertIn("   - [2026](#2026)", updated)
        self.assertNotIn("   - [2025](#2025)", updated)


if __name__ == "__main__":
    unittest.main()
