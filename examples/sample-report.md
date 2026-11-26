# SEO Audit â€” example-gastro.de

**Verdict:** The site is crawlable, but the menu and reservation templates share
titles, the location pages are orphaned, and the reservation page is missing a
canonical. Fix the template and internal linking before writing new content.

**Scope:** 18 of ~42 pages Â· 2026-11-20 Â· static HTML Â· sample report

## 1. Top 10 fixes

| # | Fix | Why it matters | Evidence | Effort | Owner |
|---:|---|---|---|---|---|
| 1 | Give the 12 menu pages unique titles | Google may pick a different page for "Speisekarte" queries | `title-duplicate`, 12 URLs | S | dev |
| 2 | Link the three location pages from the footer | They have zero inbound internal links in the crawl | `orphan-page`, 3 URLs | S | dev |
| 3 | Add a self-referencing canonical to `/reservation` | The page competes with the iframe URL | `canonical-missing` | S | dev |
| 4 | Fix the H1 on the menu template | The H1 currently repeats the brand only | `h1-missing` | S | content |
| 5 | Compress the hero image | 1.8 MB JPEG is the LCP candidate | `image-format` (PSI) | M | dev |
| 6 | Add `width`/`height` to gallery images | Mobile CLS 0.18 | `images-dimensions-missing` | S | dev |
| 7 | Add `LocalBusiness` JSON-LD with NAP | Entity consistency for local search | `jsonld-missing` | M | dev |
| 8 | Remove `noindex` from `/speisekarte/2025` | It is linked from the current menu | `noindex`, GSC sample | S | dev |
| 9 | Rewrite 4 descriptions over 170 chars | They are truncated in SERPs | `description-length` | S | content |
| 10 | Replace 9 "mehr erfahren" anchors with descriptive links | Generic anchors carry no context | `link-text-generic` | S | content |

## 2. What is already good

- HTTPS, HSTS and a valid sitemap.
- Clean URLs, no redirect chains on the main navigation.
- Menu pages have real text, not only PDFs.
- Images use descriptive file names.
- robots.txt allows the important paths.

## 3. Crawl and indexing

- 18 pages crawled, 42 in the sitemap; the sample is the public navigation.
- `/reservation` has no canonical; the iframe URL is indexable.
- `/speisekarte/2025` returns `noindex` but is linked from `/speisekarte`.
- Three location pages are not linked from any crawled page.

## 4. Templates and page clusters

| Cluster | Pages | Main issue | Fix once |
|---|---:|---|---|
| Menu | 12 | duplicate title, brand-only H1 | use dish/category as title and H1 |
| Location | 3 | orphaned | footer link + local schema |
| Reservation | 1 | no canonical | self-canonical + iframe noindex |

## 5. On-page and content

- 12 duplicate titles, 9 duplicate descriptions.
- Four descriptions exceed 170 characters.
- Two pages under 180 words; one is a legal page (acceptable).
- JSON-LD exists on the homepage but not on location pages.

## 6. Performance

- Mobile PSI: LCP 3.8 s, CLS 0.18, INP 210 ms (lab, 2026-11-20).
- Hero JPEG 1.8 MB; gallery images lack dimensions.
- No field data checked in this sample.

## 7. Search Console quick wins

- 14 queries in position 4â€“15 with â‰¥50 impressions.
- `/speisekarte` has 8,200 impressions and 1.1% CTR at position 6.
- "tisch reservieren <ort>" appears with two competing pages.

## 8. AI search note

No `llms.txt` recommendation: Google Search ignores it. AI features use normal
SEO; the page must be indexed and snippet-eligible. No special schema is
required.

## 9. 30/60/90

| Window | Focus | Done when |
|---|---|---|
| 0â€“30 days | canonical, noindex, orphan links | top 5 closed |
| 30â€“60 days | menu template, titles, descriptions | 12 pages unique |
| 60â€“90 days | LCP/CLS, LocalBusiness schema, GSC CTR test | measured |

## 10. Method and limits

- Static HTML crawl, 18 pages, depth 2, robots respected.
- No JavaScript rendering; the reservation iframe was not executed.
- No backlink index, no rank tracking, no Google scraping.
- GSC not connected in this sample.
- A crawl is not an index; verify with URL Inspection before promising fixes.
