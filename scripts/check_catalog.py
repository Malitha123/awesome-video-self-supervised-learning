import csv
import html as html_module
from html.parser import HTMLParser
import json
import re
import shlex
import sys

import yaml

from repo_tools import (
    ROOT,
    README_PATH,
    PAPERS_PATH,
    SITE_URL,
    REPO_URL,
    GOOGLE_SITE_VERIFICATION,
    normalize_title,
    extract_arxiv_id,
    parse_main_representation,
)

errors=[]
papers=json.loads(PAPERS_PATH.read_text())


class CatalogHTMLParser(HTMLParser):
    VOID_TAGS = {
        'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
        'link', 'meta', 'param', 'source', 'track', 'wbr',
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack=[]
        self.ids=set()
        self.aria_references=[]
        self.structure_errors=[]

    def handle_starttag(self, tag, attrs):
        attributes=dict(attrs)
        if attributes.get('id'):
            self.ids.add(attributes['id'])
        if attributes.get('aria-labelledby'):
            self.aria_references.extend(attributes['aria-labelledby'].split())
        if tag not in self.VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID_TAGS and self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in self.VOID_TAGS:
            return
        if not self.stack:
            self.structure_errors.append(f'unexpected closing </{tag}>')
            return
        expected=self.stack.pop()
        if expected != tag:
            self.structure_errors.append(f'closing </{tag}> encountered while <{expected}> was open')

    def finish(self):
        if self.stack:
            self.structure_errors.append('unclosed tags: ' + ', '.join(self.stack[-10:]))
        missing=sorted(set(self.aria_references)-self.ids)
        if missing:
            self.structure_errors.append('aria-labelledby references missing ids: ' + ', '.join(missing))

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
    marker=f'   - [{year}](#{year})'
    count=readme.count(marker)
    if count != 1:
        errors.append(f'README contents should contain one representation-learning link for {year}, found {count}')
if '<!-- AUTO:STATS:START -->' in readme or '\n## Repository Statistics\n' in readme:
    errors.append('README statistics should remain hidden')

html_text=(ROOT/'index.html').read_text()
html_parser=CatalogHTMLParser()
html_parser.feed(html_text)
html_parser.close()
html_parser.finish()
errors.extend(f'index.html structure error: {error}' for error in html_parser.structure_errors)
if html_text.count('<h1') != 1:
    errors.append(f"index.html should contain one H1, found {html_text.count('<h1')}")
if '<html lang="en">' not in html_text:
    errors.append('index.html is missing the English language declaration')
if f'<link rel="canonical" href="{SITE_URL}">' not in html_text:
    errors.append('canonical URL missing or incorrect')
if '<link rel="manifest" href="./site.webmanifest">' not in html_text:
    errors.append('web manifest link missing')
if f'<meta name="google-site-verification" content="{GOOGLE_SITE_VERIFICATION}">' not in html_text:
    errors.append('Google site verification metadata is missing or incorrect')
if html_text.count('<meta name="description"') != 1:
    errors.append('index.html should contain exactly one meta description')
title_match=re.search(r'<title>(.*?)</title>',html_text,flags=re.S)
title=html_module.unescape(title_match.group(1)) if title_match else ''
if not title_match or title != title.strip() or not 30 <= len(title) <= 65:
    errors.append('SEO title should be present and between 30 and 65 characters')
desc_match=re.search(r'<meta name="description" content="([^"]+)">',html_text)
if not desc_match or not 70 <= len(desc_match.group(1)) <= 160:
    errors.append('meta description should be present and between 70 and 160 characters')
for marker in ['property="og:site_name"','property="og:image:alt"','name="twitter:image:alt"']:
    if marker not in html_text:
        errors.append(f'missing social metadata {marker}')
if 'Common search terms covered by this resource' in html_text:
    errors.append('visible keyword-list paragraph still present in index.html')
if 'id="challenges"' in html_text:
    errors.append('Challenges section is still present in index.html')
paper_card_count=html_text.count('class="paper-card"')
if paper_card_count != len(papers):
    errors.append(f"website paper-card count {paper_card_count} != catalog count {len(papers)}")
for marker in ['id="paper-search"','id="year-filter"','id="venue-filter"','id="prev-page"','id="next-page"']:
    if marker not in html_text:
        errors.append(f'missing website catalog control {marker}')
for marker in ['id="benchmark-filter"','id="family-filter"','class="benchmark-tags"','class="method-label"','data-benchmarks=','data-family=']:
    if marker in html_text:
        errors.append(f'hidden metadata leaked into website presentation: {marker}')
if 'class="hero-meta"' in html_text:
    errors.append('duplicate hero statistics are still present')
notice_pos=html_text.find('class="publication-notice"')
stats_pos=html_text.find('id="stats"')
if notice_pos < 0 or stats_pos < 0 or notice_pos > stats_pos:
    errors.append('publication notice must appear before the collection snapshot')
for marker in ['aria-label="Publication update policy"',f'href="{REPO_URL}/pulls"']:
    if marker not in html_text:
        errors.append(f'publication notice missing {marker}')
for marker in [
    'Video SSL', 'VideoSSL', 'SSL video', 'self-supervised video representation learning',
    'UCF101', 'HMDB51', 'Kinetics-400', 'Something-Something V2', 'EPIC-KITCHENS',
    'CVPR', 'ICCV', 'ECCV', 'NeurIPS',
]:
    if marker not in html_text:
        errors.append(f'missing visible SEO coverage term {marker}')
if '**Method:**' in readme or '**Datasets:**' in readme or '**Benchmarks:**' in readme:
    errors.append('hidden per-paper metadata leaked into README')

schema_match=re.search(r'<script type="application/ld\+json">(.*?)</script>',html_text,flags=re.S)
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

ids=re.findall(r'\bid="([^"]+)"',html_text)
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

workflow_path=ROOT/'.github/workflows/weekly-curation.yml'
workflow_text=workflow_path.read_text()
if 'OPENAI_API_KEY' in workflow_text:
    errors.append('weekly workflow still references OPENAI_API_KEY')
try:
    workflow_data=yaml.safe_load(workflow_text)
except yaml.YAMLError as exc:
    errors.append(f'weekly workflow is invalid YAML: {exc}')
    workflow_data={}

if not isinstance(workflow_data,dict):
    errors.append('weekly workflow must be a YAML object')
    workflow_data={}
permissions=workflow_data.get('permissions') or {}
for permission in ['contents','pull-requests','copilot-requests']:
    if permissions.get(permission) != 'write':
        errors.append(f'weekly workflow missing {permission}: write')

run_blocks=[]
for job in (workflow_data.get('jobs') or {}).values():
    if not isinstance(job,dict):
        continue
    for step in job.get('steps') or []:
        if isinstance(step,dict) and isinstance(step.get('run'),str):
            run_blocks.append(step['run'])

curator_source=(ROOT/'scripts/curate_weekly.py').read_text()
for required_script in ['sync_catalog_audits.py','build_site.py']:
    if required_script not in curator_source:
        errors.append(f'weekly curator does not run {required_script}')

staged_targets=set()
stages_everything=False
for block in run_blocks:
    normalized=re.sub(r'\\\s*\n\s*',' ',block)
    for line in normalized.splitlines():
        stripped=line.strip()
        if not stripped.startswith('git add '):
            continue
        try:
            tokens=shlex.split(stripped)
        except ValueError as exc:
            errors.append(f'could not parse weekly workflow git add command: {exc}')
            continue
        stages_everything=stages_everything or '-A' in tokens or '--all' in tokens
        staged_targets.update(
            token.rstrip('/')
            for token in tokens[2:]
            if token not in {'--','-A','--all'} and not token.startswith('-')
        )

required_targets={
    'README.md','index.html','data','repository_stats.json','build_checks.json',
    'sitemap.xml','robots.txt','site.webmanifest','media',
}
missing_targets=sorted(required_targets-staged_targets)
if missing_targets and not stages_everything:
    errors.append('weekly workflow git add is missing: ' + ', '.join(missing_targets))

if not (ROOT/'.nojekyll').is_file():
    errors.append('branch-published Pages site is missing .nojekyll')

if errors:
    print('VALIDATION FAILED')
    for e in errors: print('-',e)
    sys.exit(1)
print(f"Validation passed: {len(papers)} canonical papers, {len(arxiv)} arXiv IDs, {progress.get('verified_paper_count', 0)} year-audited papers, interactive card website, branch-based Pages output, Copilot workflow configured.")
