# Weekly VideoSSL curation with GitHub Copilot

The repository is configured for a weekly, human-approved update cycle without requiring an OpenAI API key.

## What happens each week

1. GitHub Actions runs every Monday using the schedule in `.github/workflows/weekly-curation.yml`.
2. `scripts/curate_weekly.py` searches recent arXiv and OpenAlex records using the configured research queries.
3. Deterministic checks remove obvious duplicates using arXiv IDs, DOIs and title similarity.
4. The remaining candidates are reviewed by **GitHub Copilot CLI**. Copilot is asked to verify that each candidate is genuinely a video self-supervised learning contribution, that its own experiments use a relevant video benchmark, and that it is not an alternate title/version of an existing paper.
5. Accepted candidates are added to `data/papers.json`.
6. The README, website, statistics, sitemap and charts are rebuilt.
7. The workflow opens a pull request. It does **not** merge directly to `main`.
8. You review the pull request and merge it only when you approve the proposed additions.

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
4. In **Settings → Pages**, use **GitHub Actions** as the Pages publishing source.
5. Optional: add a repository variable named `COPILOT_MODEL` if you want to pin a specific model. Leaving it unset uses Copilot CLI's default model.

## Manual test

Open the repository's **Actions** tab, choose **Weekly VideoSSL curation agent**, then choose **Run workflow**.

If no qualifying papers are found, no pull request is created. If candidates pass review, a PR is opened with a checklist and verification links.

## Source of truth

`data/papers.json` is the canonical representation-learning catalog. The GitHub README is regenerated as the traditional year-by-year list. The website uses the same catalog but presents it as a searchable, filterable card interface with pagination.

The old Challenges/taxonomy appendix has been removed from both README and website. Method-family metadata is retained in `data/papers.json` and is still used for filtering and statistics.
