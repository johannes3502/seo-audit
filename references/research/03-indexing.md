# Crawling, indexing and canonicalization

Sources: Google canonicalization, consolidate duplicate URLs, noindex,
robots.txt, sitemaps, redirects, status codes, mobile-first indexing (see
`00-sources.md`).

## Decision table

| Goal | Correct tool | Do not use |
|---|---|---|
| Keep a page out of Search | `noindex` meta or `X-Robots-Tag` | `robots.txt` (it only blocks crawling; the URL can still appear) |
| Prevent crawling a huge/private area | `robots.txt` | `noindex` alone if the crawler cannot fetch the page |
| Consolidate duplicates | `rel="canonical"`, redirects, sitemap | `noindex` on the duplicate if you want it to remain a signal |
| Retire a page with a replacement | `301`/`308` to the closest equivalent | Redirect everything to the homepage |
| Remove a page with no replacement | `404` or `410` | A `200` page that says "not found" (soft 404) |
| Tell Google about important URLs | XML sitemap + internal links | Sitemap as the only discovery path |
| Block an asset from Googlebot | Usually do not; Google needs CSS/JS to render | Blocking `/_next/`, `/assets/`, `/static/` |

## Canonicals

- Use a self-referencing canonical on the canonical page.
- Do not use `robots.txt` for canonicalization; Google may still index a
  disallowed URL without its content.
- Do not use `noindex` to pick a canonical inside a site; it removes the page.
- Do not point hreflang variants at a canonical in a different language.
- Do not set a canonical in the raw HTML and change it later with JavaScript.
- If you cannot put it in the HTML, set it only with JavaScript and leave it
  out of the raw HTML; do not provide two conflicting values.
- Internal links and sitemap URLs should use the canonical form.

## robots.txt

- `Disallow` prevents crawling, not indexing. A disallowed URL can still be
  indexed from links, without content.
- Google follows at least five redirect hops for `robots.txt` and treats a
  redirect loop/too many hops as a 404.
- Google supports `user-agent`, `allow`, `disallow`, `sitemap`; it does not
  support `crawl-delay`.
- Blocking CSS/JS prevents Google from rendering the page properly.
- Block state-changing URLs (cart, login, account actions) rather than trying
  to canonicalize them.

## Sitemaps

- Absolute URLs, UTF-8, max 50 MB uncompressed or 50,000 URLs per file.
- Only indexable, canonical URLs. Do not include `noindex` pages.
- A sitemap is a hint, not a guarantee of crawling or indexing.
- Reference it in `robots.txt` and/or submit it in Search Console.
- Split large sites with a sitemap index.
- Use image/video/news extensions only when they add correct data.

## Redirects and status codes

- `301`/`308`: permanent; strong signal that the target should be canonical.
- `302`/`303`/`307`: temporary; weak signal; keep the old URL if the move is
  temporary.
- Google follows up to 10 redirect hops for general web crawling; chains waste
  time and crawl budget.
- `404` and `410` are treated the same for removal; `410` is clearer for
  deliberate deletion.
- `5xx` makes Google slow crawling; persistent `5xx` can remove pages.
- A `200` response does not guarantee indexing.
- Soft 404: an error/empty page served with `200`. Common in SPAs that rewrite
  unknown paths to `index.html`.
- A custom 404 page must return a real `404` status; the page is for users,
  not for indexing.

## Mobile-first indexing

Google indexes the mobile version of the page. For responsive sites the HTML is
the same, so most parity problems disappear. For dynamic serving or separate
mobile URLs, keep parity for:

- primary content, headings, images and alt text
- title and meta description
- robots meta (a mobile-only `noindex` can remove the page)
- canonical and hreflang
- structured data
- crawlable links (do not hide primary navigation behind an uncrawlable
  interaction)
- resources needed for rendering

Do not lazy-load primary content behind a click/swipe; Google does not perform
those interactions to load content. Content in accordions/tabs is fine if it is
in the HTML and does not require an interaction to load.

## Pagination, facets and crawl budget

- Paginated series: crawlable next/previous links; do not canonicalize every
  page to page 1.
- Faceted navigation: control indexable combinations; use canonical/robots/
  noindex deliberately. Do not let every filter combination become a crawlable
  page by accident.
- Internal search results: usually `noindex` and not linked as primary
  navigation.
- Orphan pages: every page you care about should have at least one crawlable
  internal link.
