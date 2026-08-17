# Weekly VideoSSL curation with GitHub Copilot

The repository is configured for a weekly, human-approved update cycle without requiring an OpenAI API key.

## What happens each week

1. GitHub Actions runs every Monday using the schedule in `.github/workflows/weekly-curation.yml`.
2. `scripts/curate_weekly.py` searches an overlapping 30-day arXiv and OpenAlex window using the configured research queries. Temporary request failures are retried with exponential backoff.
3. Deterministic checks identify unchanged duplicates and possible publication upgrades using arXiv IDs, DOIs, URLs, years and title similarity.
4. The remaining candidates are reviewed by **GitHub Copilot CLI**. Copilot is asked to verify relevance, benchmark use, complete hidden audit metadata and primary-source publication evidence.
5. A genuinely new work is added once. A later conference or journal version of an existing arXiv work updates that canonical record instead of creating a duplicate. Unchanged duplicates are rejected.
6. `scripts/sync_catalog_audits.py` synchronizes the per-year JSON/CSV audits, dynamic all-paper JSON/CSV/XLSX tables and `data/audit_progress.json`.
7. The README, website, statistics, sitemap and charts are rebuilt and validated from `data/papers.json`.
8. The workflow opens a pull request containing both public files and hidden audit records. It does **not** merge directly to `main`.
9. You review the pull request and merge it only when you approve the proposed additions and publication updates.
10. Merging to `main` triggers the GitHub Pages workflow and publishes the rebuilt website.

If every request to either discovery source fails after its retries, or if any Copilot review batch cannot be completed, the workflow exits unsuccessfully without writing a partial catalog. This distinguishes an actual no-results week from an infrastructure outage and keeps the next run eligible to search the overlapping window again.

## Authentication

No `OPENAI_API_KEY` is used.

The workflow grants:

```yaml
permissions:
  contents: write
  pull-requests: write
  copilot-requests: write
```

Copilot CLI authenticates with the short-lived `GITHUB_TOKEN` automatically provided to the Actions run. For a personally owned repository, Copilot usage is charged against the repository owner's Copilot entitlement. You therefore need an active GitHub Copilot plan, but you do not need to create or store a separate AI API secret.

## One-time GitHub settings

1. Make sure GitHub Actions is enabled for the repository.
2. Make sure your GitHub Copilot plan is active.
3. In **Settings → Actions → General**, allow workflows to create pull requests if your repository currently blocks that capability.
4. In **Settings → Pages**, use **Deploy from a branch**, select `main`, select `/(root)`, and save. The repository already contains the generated static files and `.nojekyll`.
5. Optional: add a repository variable named `COPILOT_MODEL` if you want to pin a specific model. Leaving it unset uses Copilot CLI's default model.

## Manual test

Open the repository's **Actions** tab, choose **Weekly VideoSSL curation agent**, then choose **Run workflow**.

If no qualifying paper or publication upgrade is found, no pull request is created. If a candidate passes review, a PR is opened with separate additions and publication-update tables, a checklist and verification links.

For a local, non-writing review:

```bash
python -m pip install -r requirements.txt
python scripts/curate_weekly.py --dry-run
```

Use `--lookback-days N` to expand the recovery window for a manual run, and `--verbose` for debug logging.

## Source of truth

`data/papers.json` is the canonical representation-learning catalog. `scripts/build_site.py` is the source of truth for generated public files. The GitHub README is regenerated as the traditional year-by-year list. The website uses the same catalog but presents it as a searchable, filterable card interface with pagination. The richer method and dataset fields remain in `data/` and are not rendered on public paper cards or in README entries.

Do not edit generated sections of `README.md` or `index.html` directly. Put website title, notice, verification metadata, or layout changes in `scripts/build_site.py`, rebuild, validate, and commit the source and generated outputs together.

The current all-paper audit is regenerated at `data/audits/all_canonical_papers.{json,csv,xlsx}`. The original `all_282_papers.*` files remain as the dated 2026-08-11 historical snapshot.
