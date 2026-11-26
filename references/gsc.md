# Google Search Console connector

## What the API can and cannot do

Available in the Search Console API v1:

- **Search Analytics:** clicks, impressions, CTR, position by query, page,
  country, device, date, search appearance
- **URL Inspection:** indexed version, crawl info, canonical, robots, rich
  result issues for one URL
- **Sitemaps:** list, submit, delete
- **Sites:** list properties, add/remove sites

Not available through the API:

- Page Indexing report (the UI report)
- Core Web Vitals report (use CrUX/PSI instead)
- Links report
- Manual Actions
- Indexing requests for normal pages
- Anonymous access without a Google account
- Search generative AI performance/control (UI; see below)

## Search generative AI

Search Console has a **Search generative AI control** (rollout completed
2026-08-31) and a generative AI performance report. The control includes or
excludes a site from AI Overviews/AI Mode/Discover generative features. It is
not a ranking API and does not affect model training. Treat it as a business
setting, not an SEO scoring input.

## Access model

- **OAuth 2.0 only.** No API key can read GSC data.
- The signed-in Google account needs at least read access to a **verified
  property**.
- **Scope:** `https://www.googleapis.com/auth/webmasters.readonly`
  for reading. Never use the write scope (`webmasters`) for an audit agent.
- **Service account:** works for scheduled jobs, but the service account email
  must be added as a user on the property. It sees nothing until then.
- Public apps using the scope must complete Google's verification process
  (consent screen, privacy policy, possibly security assessment).

## Setup (OAuth desktop client)

1. Create a Google Cloud project.
2. Enable the **Google Search Console API**.
3. Configure the OAuth consent screen.
4. Create an OAuth client of type **Desktop app** and download the JSON.
5. Run:

```bash
pip install google-api-python-client google-auth-oauthlib
python scripts/gsc_quick_wins.py \
  --property sc-domain:example.com \
  --client-secret client_secret.json \
  --days 90 \
  --out gsc-report
```

The script stores a refresh token in `token.json` (gitignored). Delete it to
revoke local access.

## Property string

Use the exact string from `sites.list`:

- Domain property: `sc-domain:example.com`
- URL-prefix property: `https://example.com/` (with protocol and trailing
  slash)

Do not guess. A wrong string produces `403` or `404`, not an empty result.

## Quotas and limits

| Limit | Value |
|---|---|
| Search Analytics rows per request | 25,000 |
| Search Analytics rows per day per search type | 50,000 |
| Search Analytics queries per minute per site | 1,200 |
| URL Inspection per day per site | 2,000 |
| URL Inspection per minute per site | 600 |
| Data freshness | typically 2â€“3 days delayed |
| History | 16 months |
| Filters | AND only, no OR groups |
| Rare queries | omitted by Google |

If you hit `429`, back off and retry. If you hit the daily row cap, narrow the
date range, drop dimensions, or split by page/query.

## What to compute

- **Quick wins:** position 4â€“15, impressions â‰¥ 50, sorted by impressions.
- **CTR gaps:** observed CTR well below the position benchmark; treat the
  benchmark as a heuristic.
- **Cannibalization:** one query, multiple pages with meaningful impressions.
- **Content decay:** clicks/impressions down period-over-period for the same
  page.
- **Index sample:** URL Inspection for the top 20â€“50 pages, not all pages.

## Safety rules for agents

- Read-only scope only.
- Keep credentials out of prompts and repositories.
- Cap calls; URL Inspection is the tightest quota.
- Never submit sitemaps or change properties during an audit.
- Never claim "indexed" from a crawl; only URL Inspection or the UI can say
  that.
- Do not train models on customer GSC data without explicit consent.

## Common errors

| Error | Likely cause | Fix |
|---|---|---|
| 403 | No access to property, wrong property string, or API not enabled | Check `sites.list`, add the account/service account, enable API |
| 404 | Property string mismatch | Copy exactly from `sites.list` |
| 429 | Quota exceeded | Back off, narrow range, split queries |
| `invalid_grant` | Token revoked/expired | Delete `token.json`, re-run OAuth |
| Empty rows | No data for filters/period, or property is new | Widen dates, check UI first |
| `access_denied` | OAuth consent not granted | Re-run flow, check test users |

## Privacy

GSC queries can contain personal data (names, addresses, rare searches).
Process only what is needed, store it in the EU, define retention, and delete
on request. Do not sell or share GSC data. For a public product, add a DPA/AVV
and a clear purpose limitation.
