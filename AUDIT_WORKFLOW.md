# Canonical paper audit workflow

The original 282-paper catalog was audited from the newest year to the oldest year. Each year remains a self-contained checkpoint, and the weekly curator now keeps these checkpoints synchronized as the canonical collection grows or publication records change.

## Source and decision rules

1. Search the exact paper title in Google Scholar or another scholarly index to discover later versions.
2. Verify the result against primary sources in this order: official conference proceedings, publisher or DOI metadata, the latest arXiv record and manuscript, then the official project or code repository.
3. Promote an arXiv entry to a conference or journal only when a primary source confirms the publication. A Scholar snippet alone is not sufficient.
4. Record self-supervised or backbone pretraining datasets separately from downstream evaluation datasets.
5. Record a named benchmark suite and its underlying datasets. Do not turn a task name into a dataset name and do not guess a dataset hidden behind inaccessible metadata.
6. Store the verification date and URLs so time-sensitive preprint decisions can be revisited.

## Per-year checkpoint

For each year, add `data/audits/YEAR.json` with one record for every canonical paper in that year. The audit must include method, method family, pretraining datasets, evaluation datasets, year, latest confirmed venue, publication status, and verification URLs.

After a manual edit, synchronize, rebuild and validate the checkpoint:

```bash
python scripts/sync_catalog_audits.py
python scripts/build_site.py
python scripts/check_catalog.py
```

The synchronization command updates `data/audit_progress.json`, every affected per-year JSON/CSV audit and the current all-paper JSON/CSV/XLSX tables. The weekly agent performs these steps automatically before opening a pull request.

## Completed audit

All 282 canonical papers from 2016 through 2026 were audited and verified on 2026-08-11. The final catalog contains a method, method family, separate pretraining and evaluation datasets, latest confirmed venue, publication status, and verification URLs for every paper.

The dated original snapshot remains available at:

- `data/audits/all_282_papers.csv`
- `data/audits/all_282_papers.json`
- `data/audits/all_282_papers.xlsx`

The final catalog contains 251 peer-reviewed records and 31 records retained as preprints because no exact-title archival publication was confirmed by the verification date. Future maintenance should recheck those time-sensitive preprints and then rebuild and validate the catalog.

## Current synchronized audit

The current catalog, including later additions and publication upgrades, is available at:

- `data/audits/all_canonical_papers.csv`
- `data/audits/all_canonical_papers.json`
- `data/audits/all_canonical_papers.xlsx`

For an arXiv-to-conference or journal upgrade, the canonical record is updated in place. Its previous venue and link are retained in the hidden `publication_history` field, preventing a duplicate public entry while preserving provenance.
