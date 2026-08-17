from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_OUTPUTS = [
    "README.md",
    "index.html",
    "repository_stats.json",
    "build_checks.json",
    "sitemap.xml",
    "robots.txt",
    "site.webmanifest",
]
IDEMPOTENT_OUTPUTS = TEXT_OUTPUTS + [
    "media/stats_papers_by_year.svg",
    "media/stats_papers_by_venue.svg",
]


class GeneratedSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.repo = Path(cls.tempdir.name) / "repository"
        shutil.copytree(
            ROOT,
            cls.repo,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        cls.committed = {path: (ROOT / path).read_bytes() for path in TEXT_OUTPUTS}
        env = os.environ.copy()
        env["MPLCONFIGDIR"] = str(Path(cls.tempdir.name) / "matplotlib")

        subprocess.run(
            [sys.executable, "scripts/build_site.py"],
            cwd=cls.repo,
            env=env,
            check=True,
            text=True,
            capture_output=True,
        )
        cls.first_build = {path: (cls.repo / path).read_bytes() for path in IDEMPOTENT_OUTPUTS}
        cls.validation = subprocess.run(
            [sys.executable, "scripts/check_catalog.py"],
            cwd=cls.repo,
            env=env,
            text=True,
            capture_output=True,
        )
        subprocess.run(
            [sys.executable, "scripts/build_site.py"],
            cwd=cls.repo,
            env=env,
            check=True,
            text=True,
            capture_output=True,
        )
        cls.second_build = {path: (cls.repo / path).read_bytes() for path in IDEMPOTENT_OUTPUTS}

    @classmethod
    def tearDownClass(cls):
        cls.tempdir.cleanup()

    def test_committed_text_outputs_match_the_generator(self):
        mismatches = [path for path in TEXT_OUTPUTS if self.committed[path] != self.first_build[path]]
        self.assertEqual(mismatches, [], "generated outputs are stale: " + ", ".join(mismatches))

    def test_generated_catalog_passes_the_validator(self):
        self.assertEqual(
            self.validation.returncode,
            0,
            self.validation.stdout + self.validation.stderr,
        )

    def test_second_build_is_byte_for_byte_idempotent(self):
        mismatches = [
            path for path in IDEMPOTENT_OUTPUTS
            if self.first_build[path] != self.second_build[path]
        ]
        self.assertEqual(mismatches, [], "non-idempotent outputs: " + ", ".join(mismatches))


if __name__ == "__main__":
    unittest.main()
