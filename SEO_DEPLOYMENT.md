# VideoSSL website deployment and SEO guide

## Public site structure

The repository serves two related public surfaces:

- `README.md` provides the complete year-by-year bibliography on GitHub.
- `index.html` provides the responsive GitHub Pages catalog with title search, year and venue filters, pagination, statistics and research resources.

Per-paper dataset and method-category fields remain in the structured `data/` and audit files. They are not rendered on paper cards or in the README. The website contains one concise research-coverage section with field terminology, representative dataset names and venue names so that readers and search engines can understand the collection's scope.

## SEO implemented in the generator

Running `python3 scripts/build_site.py` regenerates the following:

- a concise, descriptive page title and meta description;
- one clear H1 and a semantic heading hierarchy;
- canonical, robots, Open Graph and Twitter metadata;
- `WebSite`, `CollectionPage`, `ItemList`, `ScholarlyArticle` and visible FAQ JSON-LD;
- every current canonical paper title, author list, year and venue in crawlable static HTML;
- a publication-review notice whose date follows the latest verified catalog record;
- descriptive image alternative text and lazy-loaded statistics images;
- `robots.txt`, `sitemap.xml` and `site.webmanifest`;
- `build_checks.json`, which records the generated SEO checks.

The page uses natural research language such as Video SSL, VideoSSL, SSL video, self-supervised video learning and masked video modeling. It also identifies representative datasets and venues in useful prose. It does not use a meta-keywords tag or a hidden keyword list, because Google ignores meta keywords and recommends prominent, people-first content instead.

## Deploy with GitHub Pages

1. Push the project contents to the root of `Malitha123/awesome-video-self-supervised-learning`.
2. In the repository, open **Settings → Pages**, choose **Deploy from a branch**, select `main`, select `/(root)`, and save.
3. Merge an approved curation pull request. The pull request already contains the rebuilt site, and GitHub's built-in `pages build and deployment` workflow publishes the root of `main`.
4. Confirm that the canonical website, `robots.txt` and `sitemap.xml` load successfully.

The previous custom `Deploy VideoSSL website` workflow was removed because it duplicated the working branch deployment and failed whenever Pages was configured to deploy from a branch.

## Complete search-engine setup after deployment

1. Add the GitHub Pages URL as a property in [Google Search Console](https://search.google.com/search-console/about).
2. Submit `https://malitha123.github.io/awesome-video-self-supervised-learning/sitemap.xml` in the Sitemaps report.
3. Use URL Inspection to request indexing of the canonical homepage after this release.
4. Monitor indexing, query impressions, click-through rate and structured-data errors.
5. Add the site to [Bing Webmaster Tools](https://www.bing.com/webmasters/about) and submit the same sitemap.
6. Link to the catalog from the associated survey page, author profiles, lab pages and relevant research repositories where appropriate.

Google's current guidance is documented in [Search Essentials](https://developers.google.com/search/docs/essentials), the [SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide), [structured-data policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies) and [sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).

No implementation can guarantee a ranking for every query. Search visibility also depends on successful indexing, useful inbound links, site authority, query competition and continued maintenance.
