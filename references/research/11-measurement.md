# Measurement, GSC and evidence quality

Sources: Google Search Console documentation; See `gsc.md` for API scopes and
quotas. Third-party tool claims are not evidence about Google's index.

## Evidence hierarchy

1. **Deterministic code/HTML facts**: status code, raw HTML, canonical, robots,
   JSON-LD syntax. Strongest for a code review.
2. **Crawl facts**: what the server returns for a URL, redirect chains,
   sitemap/robots contents. Still not an index.
3. **Field data**: CrUX/PSI/Search Console Core Web Vitals. Real users, delayed,
   aggregated.
4. **Search Console performance**: impressions, clicks, CTR, average position.
   Query/page data is sampled and can be withheld for privacy.
5. **Third-party estimates**: keyword volume, difficulty, backlinks, "AI
   visibility". Useful for prioritization, never a Google fact.

## Search Console

- Verify the property (domain property or URL-prefix property).
- Use the exact property string from `sites.list`; never guess.
- OAuth scope `https://www.googleapis.com/auth/webmasters.readonly`; never ask
  for write scope.
- Data is typically delayed 2-3 days.
- Search Analytics API row limits: 25,000 rows per request (pagination needed),
  50,000 rows/day per search type, 1,200 queries/minute per user.
- URL Inspection API: 2,000 inspections/day per property.
- There is no API for the Indexing report, Core Web Vitals report or Links
  report; those are UI-only or need other data sources.
- The Generative AI performance report is separate; it is not a ranking API.
- `sites.list` tells you which properties the authenticated user can access.

## What GSC can support

- queries/pages with high impressions and low CTR (a hypothesis, not proof that
  the title is the cause)
- pages ranking 4-15 for a query (quick-win candidates)
- pages competing for the same query (cannibalization candidates)
- mobile vs desktop differences
- country/device/search-type segmentation
- Core Web Vitals field status
- indexing status per URL (URL Inspection)

## What GSC cannot support

- "This change caused +X traffic" without a controlled comparison.
- A full list of all queries or all pages.
- A guarantee that a URL is indexed.
- A complete backlink profile.
- A ranking factor weight.
- Any claim about AI training or AI ranking.

## Reporting rules

- Every number needs a source and a date range.
- Label estimates as estimates.
- Separate observation from recommendation.
- Do not compare two sites with different page caps as if the scores were a
  controlled benchmark.
- Do not promise rankings, traffic or revenue.
- For code changes, define a verification step: build/test, re-scan, deploy,
  then compare the same URLs and metrics.

## Baseline template

Before changing code, record:

- URL set and template groups
- raw HTML status for the key routes (title/H1/canonical/text)
- current CWV field status for the origin/templates
- GSC date range, property, device/country filters
- top queries/pages for the money pages
- known redirects, sitemap count, robots rules
- build/test commands and the commit/version

After the change, repeat the same set and state what changed. A code review can
prove the HTML changed; only measurement can show whether Search performance
changed.
