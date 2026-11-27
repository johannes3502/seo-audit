# Live-domain checklist

Run this only when the user gives a real domain. It complements the codebase
scan; it does not replace it.

## Before the crawl

- [ ] Confirm the exact origin (http/https, www/non-www, subdomain).
- [ ] Confirm permission to crawl; respect `robots.txt`.
- [ ] Choose a page cap and depth; state it in the report.
- [ ] Check whether the site is JS-rendered; the live scanner is static HTML.
- [ ] Do not crawl behind a login, paywall or bot protection.

## Raw HTML per key route

- [ ] Status 200 (or the intended 3xx/4xx).
- [ ] Title present, unique, descriptive.
- [ ] Meta description present.
- [ ] Canonical present and self-referential (or intentionally cross-canonical).
- [ ] Robots meta / `X-Robots-Tag` intended.
- [ ] One H1 and a logical heading outline.
- [ ] Primary text present without JavaScript.
- [ ] Internal links are real `<a href>`.
- [ ] Images have alt/dimensions; hero not lazy.
- [ ] JSON-LD valid and matches visible content.
- [ ] `lang` matches the URL language prefix (`/en/` → `lang="en"`).
- [ ] `hreflang` cluster in HTML and/or sitemap, with self-reference.
- [ ] No mixed content.

## Intentional noindex and CSR

- [ ] App/auth pages (`/login`, `/services`, dashboards) are `noindex`; their
      missing H1/canonical/JSON-LD/thin content is not a marketing defect.
- [ ] On a CSR shell, one `csr-shell` root cause is reported; missing H1,
      canonical, links and duplicate shell titles are symptoms, not separate
      high defects.
- [ ] An unknown URL on an SPA returns 404/410, not a 200 shell or redirect to
      home.
- [ ] A `www`/non-www alias does not serve 200 without a redirect or canonical.
- [ ] Draft/placeholder detection ignores product vocabulary such as
      "Draft Mode"; only low-content or explicit placeholder pages count.

## Site-level

- [ ] `robots.txt` returns 200; rules and sitemap line correct.
- [ ] Sitemap returns 200; URLs are canonical and indexable.
- [ ] Canonical, sitemap URLs and robots `Sitemap:` line use the same final
      host; a www/non-www mismatch is reported, not silently accepted.
- [ ] The other host alias (`www` or apex) redirects or serves a matching
      canonical; a 200 duplicate is a finding.
- [ ] Unknown URL returns 404/410, not 200; compare the body with the built
      404 page if a custom one exists.
- [ ] Redirect chains and HTTP→HTTPS canonicalization.
- [ ] Duplicate titles/descriptions across crawled pages.
- [ ] Orphan pages in the crawl.
- [ ] hreflang clusters (if multilingual).
- [ ] Legal pages that are `noindex` are excluded from the sitemap and treated
      as an intentional policy, not a defect.
- [ ] Event JSON-LD has no past `endDate` still marked `EventScheduled`.
- [ ] Event markup is on a dedicated single-event URL, not a homepage/list
      `ItemList`; organizer and location are real.
- [ ] `LocalBusiness` NAP (name, address, phone, hours) matches the visible
      page, imprint and profile; address tokens are visible on the page.
- [ ] Legal links (imprint, privacy, terms) stay on the same host/entity; a
      cross-domain legal link is verified, not assumed.
- [ ] A `Disallow` path is not treated as deindexed; sitemap URLs are crawlable
      and a `noindex` is on a crawlable URL.
- [ ] `/index.html` is not a second indexable copy of `/`.
- [ ] Header/footer are outside `<main>` (banner/contentinfo landmarks).
- [ ] `og:locale:alternate` has a crawlable alternate URL and hreflang.
- [ ] `www`/non-www, canonical, sitemap and robots agree on the final host.
- [ ] Word/script counts are per URL and labeled as raw-HTML counts.
- [ ] CDN/firewall allows Googlebot and assets.

## Performance

- [ ] TTFB, HTML size, script count, stylesheet count.
- [ ] LCP candidate (image/text) is discoverable and prioritized.
- [ ] Field CWV from CrUX/PSI if available; do not infer from lab only.

## Report

- [ ] Page cap, sample and coverage (crawled vs sitemap URLs) stated.
- [ ] Every finding has URL + rule + evidence.
- [ ] False positives removed or marked `likely`.
- [ ] A single TTFB sample is not reported as a confirmed performance defect.
- [ ] "Crawl is not an index" stated.
- [ ] Top 3 actions and biggest uncertainty.
