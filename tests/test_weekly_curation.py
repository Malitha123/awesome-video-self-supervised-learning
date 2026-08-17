from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from curate_weekly import (  # noqa: E402
    DiscoveryUnavailableError,
    DiscoverySourceError,
    apply_verified_update,
    discover_candidates,
    find_existing_match,
    main as curate_main,
    paper_validation_errors,
    publication_candidate_needs_review,
    request_with_retries,
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

    def test_readme_year_links_handle_trailing_spaces_without_duplicates(self):
        readme = (
            "- [Representation Learning](#Representation-Learning)\n"
            "   - [2026](#2026)\n"
            "   - [2025](#2025)\n"
            "   - [2024](#2024)\n"
            "   - [2023](#2023)\n"
            "   - [2022](#2022)\n"
            "   - [2021](#2021)\n"
            "   - [2020](#2020)\n"
            "   - [2019](#2019) \n"
            "   - [2018](#2018)\n"
            "- [Surveys](#Surveys)\n"
        )
        updated = replace_representation_year_links(
            readme,
            [{"year": year} for year in range(2027, 2017, -1)],
        )
        for year in range(2027, 2017, -1):
            self.assertEqual(updated.count(f"   - [{year}](#{year})"), 1)
        self.assertNotIn("\n- [2026](#2026)", updated)

    def test_discovery_fails_when_a_source_is_completely_unavailable(self):
        def unavailable(*_args, **_kwargs):
            raise DiscoverySourceError("service unavailable")

        def succeeds(*_args, **_kwargs):
            return []

        config = {
            "search_queries": ["video ssl"],
            "request_attempts": 1,
            "retry_backoff_seconds": 0,
        }
        with self.assertLogs("videossl.curator", level="WARNING"):
            with self.assertRaisesRegex(DiscoveryUnavailableError, "arXiv"):
                discover_candidates(
                    config,
                    datetime.now(timezone.utc),
                    arxiv_search=unavailable,
                    openalex_search=succeeds,
                    sleep_fn=lambda _seconds: None,
                )

    def test_request_retries_then_returns_success(self):
        class FakeRequestException(Exception):
            response = None

        response = Mock()
        response.raise_for_status.return_value = None
        fake_requests = types.ModuleType("requests")
        fake_requests.RequestException = FakeRequestException
        fake_requests.get = Mock(side_effect=[FakeRequestException("temporary"), response])
        with self.assertLogs("videossl.curator", level="WARNING"):
            with patch.dict(sys.modules, {"requests": fake_requests}), patch("curate_weekly.time.sleep") as sleep:
                result = request_with_retries(
                    "https://example.org/api",
                    params={"q": "video ssl"},
                    attempts=2,
                    backoff_seconds=0.25,
                )
        self.assertIs(result, response)
        self.assertEqual(fake_requests.get.call_count, 2)
        sleep.assert_called_once_with(0.25)

    def test_request_does_not_retry_non_transient_http_error(self):
        class FakeRequestException(Exception):
            def __init__(self, message, response=None):
                super().__init__(message)
                self.response = response

        error_response = Mock(status_code=400, headers={})
        fake_requests = types.ModuleType("requests")
        fake_requests.RequestException = FakeRequestException
        fake_requests.get = Mock(
            side_effect=FakeRequestException("bad request", response=error_response)
        )
        with patch.dict(sys.modules, {"requests": fake_requests}), patch(
            "curate_weekly.time.sleep"
        ) as sleep:
            with self.assertRaisesRegex(DiscoverySourceError, "after 1 attempt"):
                request_with_retries(
                    "https://example.org/api",
                    params={"q": "video ssl"},
                    attempts=3,
                    backoff_seconds=0.25,
                )
        self.assertEqual(fake_requests.get.call_count, 1)
        sleep.assert_not_called()

    def test_copilot_batch_failure_makes_the_run_fail(self):
        candidate = conference_candidate()
        config = {"lookback_days": 30, "max_candidates": 40, "copilot_batch_size": 8}
        with patch("curate_weekly.load_config", return_value=config), patch(
            "curate_weekly.load_papers", return_value=[]
        ), patch("curate_weekly.discover_candidates", return_value=[candidate]), patch(
            "curate_weekly.verify_batch_with_copilot", side_effect=RuntimeError("Copilot unavailable")
        ), self.assertLogs("videossl.curator", level="ERROR"):
            result = curate_main([])
        self.assertEqual(result, 3)

    def test_dry_run_never_writes_catalog_or_generated_files(self):
        candidate = conference_candidate()
        verdict = conference_verdict()
        verdict.update({"action": "add", "existing_normalized_title": ""})
        config = {"lookback_days": 30, "max_candidates": 40, "copilot_batch_size": 8}
        with patch("curate_weekly.load_config", return_value=config), patch(
            "curate_weekly.load_papers", return_value=[]
        ), patch("curate_weekly.discover_candidates", return_value=[candidate]), patch(
            "curate_weekly.verify_batch_with_copilot", return_value=[verdict]
        ), patch("curate_weekly.save_papers") as save, patch(
            "curate_weekly.subprocess.run"
        ) as run, patch("curate_weekly.write_pr_body") as write_pr_body, self.assertLogs(
            "videossl.curator", level="INFO"
        ):
            result = curate_main(["--dry-run"])
        self.assertEqual(result, 0)
        save.assert_not_called()
        run.assert_not_called()
        write_pr_body.assert_not_called()


if __name__ == "__main__":
    unittest.main()
