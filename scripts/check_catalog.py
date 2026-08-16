from pathlib import Path
import csv
from datetime import datetime
import json
import re
import sys

from repo_tools import ROOT, README_PATH, PAPERS_PATH, SITE_URL, REPO_URL, normalize_title, extract_arxiv_id, parse_main_representation

errors=[]
papers=json.loads(PAPERS_PATH.read_text())


def display_date(value):
    parsed=datetime.strptime(value,'%Y-%m-%d')
    return f"{parsed.day} {parsed.strftime('%B %Y')}"

progress_path=ROOT/'data/audit_progress.json'
if not progress_path.exists():
    errors.append('missing data/audit_progress.json')
    progress={}
else:
    progress=json.loads(progress_path.read_text())

titles={}
for p in papers:
    key=normalize_title(p['title'])
    if key in titles:
        errors.append(f"duplicate normalized title: {p['title']} / {titles[key]}")
    titles[key]=p['title']

arxiv={}
for p in papers:
    aid=p.get('arxiv_id') or extract_arxiv_id(p.get('paper_url',''),p.get('venue',''))
    if aid:
        if aid in arxiv:
            errors.append(f"duplicate arXiv id {aid}: {p['title']} / {arxiv[aid]}")
        arxiv[aid]=p['title']

if progress:
    if progress.get('canonical_paper_count') != len(papers):
        errors.append(
            f"audit progress canonical count {progress.get('canonical_paper_count')} != {len(papers)}"
        )
    completed_years=progress.get('completed_years') or []
    verified=0
    for year in completed_years:
        audit_path=ROOT/f'data/audits/{year}.json'
        csv_path=ROOT/f'data/audits/{year}.csv'
        if not audit_path.exists():
            errors.append(f'missing audit file for completed year {year}')
            continue
        audit=json.loads(audit_path.read_text())
        year_papers=[p for p in papers if p.get('year') == year]
        if audit.get('status') != 'complete':
            errors.append(f'audit status for {year} is not complete')
        if audit.get('paper_count') != len(year_papers):
            errors.append(
                f"audit {year} paper_count {audit.get('paper_count')} != catalog count {len(year_papers)}"
            )
        audit_titles={r.get('normalized_title') for r in audit.get('records', [])}
        catalog_titles={p.get('normalized_title') or normalize_title(p['title']) for p in year_papers}
        if audit_titles != catalog_titles:
            errors.append(f'audit title set does not match catalog for {year}')
        for p in year_papers:
            verified += 1
            for field in [
                'method', 'method_family', 'pretraining_datasets', 'evaluation_datasets',
                'datasets', 'venue', 'venue_normalized', 'publication_status',
                'verification_urls', 'venue_evidence',
            ]:
                if not p.get(field):
                    errors.append(f"audited paper missing {field}: {p['title']}")
            if p.get('audit_status') != 'verified' or p.get('audit_year') != year:
                errors.append(f"invalid audit marker: {p['title']}")
            status=p.get('publication_status')
            is_preprint=p.get('venue_normalized') == 'arXiv / Preprint'
            if status == 'preprint' and not is_preprint:
                errors.append(f"preprint status conflicts with venue: {p['title']}")
            if status == 'peer_reviewed' and is_preprint:
                errors.append(f"peer-reviewed status conflicts with venue: {p['title']}")
        if not csv_path.exists():
            errors.append(f'missing audit CSV for completed year {year}')
        else:
            with csv_path.open(newline='') as f:
                row_count=sum(1 for _ in csv.reader(f)) - 1
            if row_count != len(year_papers):
                errors.append(f'audit CSV row count {row_count} != catalog count {len(year_papers)} for {year}')
    if progress.get('verified_paper_count') != verified:
        errors.append(
            f"audit progress verified count {progress.get('verified_paper_count')} != {verified}"
        )
    if progress.get('remaining_paper_count') != len(papers)-verified:
        errors.append('audit progress remaining count is inconsistent')

    master_json_path=ROOT/progress.get('master_json','')
    master_csv_path=ROOT/progress.get('master_csv','')
    master_xlsx_path=ROOT/progress.get('master_xlsx','')
    if not master_json_path.is_file():
        errors.append('current master audit JSON is missing')
    else:
        try:
            master=json.loads(master_json_path.read_text())
            master_titles={normalize_title(record.get('title','')) for record in master.get('records',[])}
            if master.get('canonical_paper_count') != len(papers):
                errors.append('current master audit JSON count does not match catalog')
            if master_titles != set(titles):
                errors.append('current master audit JSON titles do not match catalog')
        except json.JSONDecodeError as exc:
            errors.append(f'invalid current master audit JSON: {exc}')
    if not master_csv_path.is_file():
        errors.append('current master audit CSV is missing')
    else:
        with master_csv_path.open(newline='',encoding='utf-8') as handle:
            master_csv_count=sum(1 for _ in csv.reader(handle))-1
        if master_csv_count != len(papers):
            errors.append('current master audit CSV count does not match catalog')
    if not master_xlsx_path.is_file():
        errors.append('current master audit XLSX is missing')

readme=README_PATH.read_text()
if 'Common search terms covered by this resource' in readme:
    errors.append('visible keyword-list paragraph still present in README')
if '\n# Challenges\n' in readme:
    errors.append('Challenges section is still present in README')
parsed=parse_main_representation(readme)
if len(parsed) != len(papers):
    errors.append(f"README canonical list count {len(parsed)} != data/papers.json count {len(papers)}")
for year in sorted({p.get('year') for p in papers if p.get('year')},reverse=True):
    if f'   - [{year}](#{year})' not in readme:
        errors.append(f'README contents missing representation-learning year {year}')

html=(ROOT/'index.html').read_text()
if html.count('<h1') != 1:
    errors.append(f"index.html should contain one H1, found {html.count('<h1')}")
if '<html lang="en">' not in html:
    errors.append('index.html is missing the English language declaration')
if f'<link rel="canonical" href="{SITE_URL}">' not in html:
    errors.append('canonical URL missing or incorrect')
if '<link rel="manifest" href="./site.webmanifest">' not in html:
    errors.append('web manifest link missing')
if html.count('<meta name="description"') != 1:
    errors.append('index.html should contain exactly one meta description')
title_match=re.search(r'<title>(.*?)</title>',html,flags=re.S)
if not title_match or not 30 <= len(title_match.group(1)) <= 65:
    errors.append('SEO title should be present and between 30 and 65 characters')
desc_match=re.search(r'<meta name="description" content="([^"]+)">',html)
if not desc_match or not 70 <= len(desc_match.group(1)) <= 160:
    errors.append('meta description should be present and between 70 and 160 characters')
for marker in ['property="og:site_name"','property="og:image:alt"','name="twitter:image:alt"']:
    if marker not in html:
        errors.append(f'missing social metadata {marker}')
if 'Common search terms covered by this resource' in html:
    errors.append('visible keyword-list paragraph still present in index.html')
if 'id="challenges"' in html:
    errors.append('Challenges section is still present in index.html')
paper_card_count=html.count('class="paper-card"')
if paper_card_count != len(papers):
    errors.append(f"website paper-card count {paper_card_count} != catalog count {len(papers)}")
for marker in ['id="paper-search"','id="year-filter"','id="venue-filter"','id="prev-page"','id="next-page"']:
    if marker not in html:
        errors.append(f'missing website catalog control {marker}')
for marker in ['id="benchmark-filter"','id="family-filter"','class="benchmark-tags"','class="method-label"','data-benchmarks=','data-family=']:
    if marker in html:
        errors.append(f'hidden metadata leaked into website presentation: {marker}')
if 'class="hero-meta"' in html:
    errors.append('duplicate hero statistics are still present')
notice_pos=html.find('class="publication-notice"')
stats_pos=html.find('id="stats"')
if notice_pos < 0 or stats_pos < 0 or notice_pos > stats_pos:
    errors.append('publication notice must appear before the collection snapshot')
review_dates=[str(p.get('audited_at','')) for p in papers]
review_date=max((value for value in review_dates if re.fullmatch(r'\d{4}-\d{2}-\d{2}',value)),default='2026-08-11')
for marker in [f'datetime="{review_date}"',display_date(review_date),f'href="{REPO_URL}/pulls"']:
    if marker not in html:
        errors.append(f'publication notice missing {marker}')
for marker in [
    'Video SSL', 'VideoSSL', 'SSL video', 'self-supervised video representation learning',
    'UCF101', 'HMDB51', 'Kinetics-400', 'Something-Something V2', 'EPIC-KITCHENS',
    'CVPR', 'ICCV', 'ECCV', 'NeurIPS',
]:
    if marker not in html:
        errors.append(f'missing visible SEO coverage term {marker}')
if '**Method:**' in readme or '**Datasets:**' in readme or '**Benchmarks:**' in readme:
    errors.append('hidden per-paper metadata leaked into README')

schema_match=re.search(r'<script type="application/ld\+json">(.*?)</script>',html,flags=re.S)
if not schema_match:
    errors.append('JSON-LD structured data missing')
else:
    try:
        schema=json.loads(schema_match.group(1))
        graph=schema.get('@graph') or []
        graph_types={node.get('@type') for node in graph}
        for expected in ['WebSite','CollectionPage','ItemList','FAQPage']:
            if expected not in graph_types:
                errors.append(f'JSON-LD missing {expected}')
        item_list=next((node for node in graph if node.get('@type') == 'ItemList'),{})
        items=item_list.get('itemListElement') or []
        if item_list.get('numberOfItems') != len(papers) or len(items) != len(papers):
            errors.append('JSON-LD paper list does not match canonical catalog count')
        scholarly=sum(1 for item in items if (item.get('item') or {}).get('@type') == 'ScholarlyArticle')
        if scholarly != len(papers):
            errors.append(f'JSON-LD ScholarlyArticle count {scholarly} != {len(papers)}')
    except (json.JSONDecodeError,TypeError) as exc:
        errors.append(f'invalid JSON-LD: {exc}')

ids=re.findall(r'\bid="([^"]+)"',html)
duplicate_ids=sorted({value for value in ids if ids.count(value) > 1})
if duplicate_ids:
    errors.append(f'duplicate HTML ids: {", ".join(duplicate_ids)}')

for f in ['stats_papers_by_year.svg','stats_papers_by_venue.svg']:
    if not (ROOT/'media'/f).exists():
        errors.append(f'missing chart {f}')
for f in ['robots.txt','sitemap.xml','site.webmanifest','repository_stats.json','build_checks.json']:
    if not (ROOT/f).exists():
        errors.append(f'missing generated file {f}')
if (ROOT/'site.webmanifest').exists():
    try:
        manifest=json.loads((ROOT/'site.webmanifest').read_text())
        for field in ['name','short_name','start_url','display','theme_color']:
            if not manifest.get(field):
                errors.append(f'web manifest missing {field}')
    except json.JSONDecodeError as exc:
        errors.append(f'invalid web manifest: {exc}')
if (ROOT/'robots.txt').exists() and f'Sitemap: {SITE_URL}sitemap.xml' not in (ROOT/'robots.txt').read_text():
    errors.append('robots.txt does not advertise the sitemap')

workflow=(ROOT/'.github/workflows/weekly-curation.yml').read_text()
if 'OPENAI_API_KEY' in workflow:
    errors.append('weekly workflow still references OPENAI_API_KEY')
if 'copilot-requests: write' not in workflow:
    errors.append('weekly workflow missing copilot-requests: write')
if 'sync_catalog_audits.py' not in (ROOT/'scripts/curate_weekly.py').read_text():
    errors.append('weekly curator does not synchronize hidden audit records')
if 'git add README.md index.html data/' not in workflow:
    errors.append('weekly workflow does not stage synchronized audit data')

if not (ROOT/'.nojekyll').is_file():
    errors.append('branch-published Pages site is missing .nojekyll')

if errors:
    print('VALIDATION FAILED')
    for e in errors: print('-',e)
    sys.exit(1)
print(f"Validation passed: {len(papers)} canonical papers, {len(arxiv)} arXiv IDs, {progress.get('verified_paper_count', 0)} year-audited papers, interactive card website, branch-based Pages output, Copilot workflow configured.")
