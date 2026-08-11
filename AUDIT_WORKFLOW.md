# Canonical paper audit workflow

The 282-paper catalog is audited from the newest year to the oldest year. Each finished year is a self-contained checkpoint, so a later session can resume without repeating completed research.

## Source and decision rules

1. Search the exact paper title in Google Scholar or another scholarly index to discover later versions.
2. Verify the result against primary sources in this order: official conference proceedings, publisher or DOI metadata, the latest arXiv record and manuscript, then the official project or code repository.
3. Promote an arXiv entry to a conference or journal only when a primary source confirms the publication. A Scholar snippet alone is not sufficient.
4. Record self-supervised or backbone pretraining datasets separately from downstream evaluation datasets.
5. Record a named benchmark suite and its underlying datasets. Do not turn a task name into a dataset name and do not guess a dataset hidden behind inaccessible metadata.
6. Store the verification date and URLs so time-sensitive preprint decisions can be revisited.

## Per-year checkpoint

For each year, add `data/audits/YEAR.json` with one record for every canonical paper in that year. The audit must include method, method family, pretraining datasets, evaluation datasets, year, latest confirmed venue, publication status, and verification URLs.

Apply, rebuild, and validate the checkpoint:

```bash
python scripts/apply_year_audit.py YEAR
python scripts/build_site.py
python scripts/check_catalog.py
```

After validation, update `data/audit_progress.json` and export the compact `data/audits/YEAR.csv` review table. Archive the entire project before starting the next year.

## Completed audit

All 282 canonical papers from 2016 through 2026 were audited and verified on 2026-08-11. The final catalog contains a method, method family, separate pretraining and evaluation datasets, latest confirmed venue, publication status, and verification URLs for every paper.

The complete review tables are available at:

- `data/audits/all_282_papers.csv`
- `data/audits/all_282_papers.json`
- `data/audits/all_282_papers.xlsx`

The final catalog contains 251 peer-reviewed records and 31 records retained as preprints because no exact-title archival publication was confirmed by the verification date. Future maintenance should recheck those time-sensitive preprints and then rebuild and validate the catalog.
