# Repository rule catalog

Rules emitted by `repo_scan.py`. `confirmed` = the pattern and location are in
the source; `likely` = framework behavior or inheritance may change the result;
`hypothesis` = requires rendered/live verification.

## Rendering

| ID | Severity | Evidence | Fix | Confidence |
|---|---|---|---|---|
| `csr-only-app` | high/medium | framework/config | Add SSR/SSG or verify prerender output | confirmed |
| `csr-only-shell` | high/medium | empty mount in `index.html` | Verify built HTML; otherwise prerender | confirmed |
| `client-page` | high | `"use client"` on a route | Keep public content in a server component | likely |
| `ssr-disabled` | high | `ssr: false` | Remove for public routes | confirmed/likely |
| `client-only-island` | medium | `client:only` | Server-render indexable content | likely |

## Metadata and on-page

| ID | Severity | Evidence | Fix | Confidence |
|---|---|---|---|---|
| `title-missing-in-route` | high/medium | no title in route | Add route-specific title | likely |
| `title-generic` | high | "Home", "Untitled", "React App" | Write a descriptive title | confirmed |
| `title-long` | low | >65 chars | Front-load the topic; shorten the brand | confirmed |
| `title-duplicate` | high | same title on routes | Unique title per intent | confirmed |
| `description-missing-in-route` | medium/low | no description | Add a unique summary | likely |
| `description-long` | low | >170 chars | Main point in 120-160 chars | confirmed |
| `description-duplicate` | medium | same description | Unique description per route | confirmed |
| `h1-missing-in-route` | medium | no H1 | Add one descriptive H1 | likely |
| `h1-multiple-in-route` | medium | >1 H1 | Keep one H1 | confirmed |
| `h1-in-layout` | medium | H1 in shared layout/header | Use non-heading markup for the logo | likely |
| `global-noindex` | critical | `noindex` in layout | Remove from shared layout | confirmed |
| `global-canonical` | high | one canonical in layout | Generate per route | likely |

## Indexing and routing

| ID | Severity | Evidence | Fix | Confidence |
|---|---|---|---|---|
| `robots-blocks-all` | critical | `Disallow: /` | Allow public pages | confirmed |
| `robots-blocks-assets` | high | blocks `/_next`, `/static`, `/assets` | Allow rendering assets | confirmed |
| `robots-no-sitemap` | low | no `Sitemap:` | Add absolute sitemap URL | confirmed |
| `robots-missing` | low | no `robots.txt` | Add robots.txt | confirmed |
| `sitemap-missing` | low | no generator/file | Generate sitemap | confirmed |
| `not-found-missing` | medium | no 404 route | Add a real 404 | likely |
| `spa-fallback` | high | catch-all to index.html | Return real 404 | likely |
| `hreflang-missing` | medium | i18n config, no hreflang | Add reciprocal hreflang | likely |
| `hreflang-missing-in-html` | low | sitemap has alternates, HTML has none | Add HTML alternates, keep sitemap | confirmed |
| `hreflang-invalid` | medium | invalid code | ISO 639-1 + optional region | confirmed |
| `soft-404-redirect` | medium | catch-all `*` redirects home | Add a real 404 route/status | confirmed |
| `scan-scope` | info | umbrella/docs/backend/no routes | Scan each app root separately | confirmed |
| `internal-not-scored` | info | internal app with noindex/Disallow | Check accidental indexability only | confirmed |
| `backend-not-scored` | info | API service without HTML | Pair with frontend/live URL | confirmed |
| `not-an-app` | info | docs/context/local tool | Use as context, not a website | confirmed |

## Media and links

| ID | Severity | Evidence | Fix | Confidence |
|---|---|---|---|---|
| `image-alt-missing` | medium | no `alt` | Describe the image; `alt=""` if decorative | confirmed |
| `image-dimensions-missing` | low | no width/height | Set dimensions/aspect ratio | confirmed |
| `lcp-image-lazy` | medium | first image `loading="lazy"` | Eager-load the LCP image | likely |
| `link-not-crawlable` | medium | `href="#"`, empty, javascript | Use a real `<a href>` | confirmed |
| `anchor-text-generic` | low | "click here", "read more" | Descriptive anchor | confirmed |
| `css-import` | low | CSS `@import` | Bundle critical CSS | confirmed |
| `third-party-fonts` | low | Google Fonts | Self-host/preload | confirmed |
| `many-stylesheets` | low | >5 stylesheets | Bundle/defer CSS | confirmed |
| `blocking-scripts` | low | no defer/async/module | Defer non-critical JS | confirmed |

## Structured data

| ID | Severity | Evidence | Fix | Confidence |
|---|---|---|---|---|
| `jsonld-invalid` | medium | parse error | Fix JSON | confirmed |
| `schema-article-fields` | low | missing headline/image/date/author | Add true fields | likely |
| `schema-product-fields` | medium | missing name/offers | Add true price/availability | likely |
| `schema-localbusiness-fields` | medium | missing name/address | Add name/PostalAddress | likely |
| `schema-faq-fields` | medium | no mainEntity | Mark up visible FAQs | likely |

## Keywords

| ID | Severity | Evidence | Fix | Confidence |
|---|---|---|---|---|
| `keyword-route-not-found` | low | map URL has no route | Fix map/route | likely |
| `keyword-target-no-metadata` | medium | map target, no title/H1 | Add metadata/H1 | likely |
| `keyword-missing-in-field` | medium | target missing from title/H1/description | Use it naturally | likely |
| `keyword-stuffing` | low | repeated target in title | Write for people | confirmed |
| `keyword-cannibalization` | high | same target on >1 URL | Choose one owner | likely |

## Local, trust and events (v0.4)

| ID | Severity | Evidence | Fix | Confidence |
|---|---|---|---|---|
| `canonical-shared` | medium | 2+ public routes share one canonical | generate a self-canonical per route | likely |
| `sitemap-lastmod-build-time` | low | `lastmod` uses `new Date()`/`Date.now()` | use the page's real modification date | likely |
| `robots-blocks-noindex` | medium | `Disallow` path also has noindex | allow crawling so noindex is readable, or use auth | confirmed |
| `robots-blocks-public-route` | high | public route under `Disallow` | allow it or add noindex; Disallow is not deindexing | confirmed |
| `client-only-i18n` | info | locale files/switcher, no locale URLs | add locale routes first; do not add hreflang yet | confirmed |
| `schema-event-fields` | medium | Event missing name/startDate/location | add only fields that match the visible event | likely |
| `schema-event-list` | medium | ItemList contains Events | one leaf URL per event, or remove Event markup | likely |
| `schema-localbusiness-recommended` | low | missing phone/hours/sameAs | add real NAP data and verified profiles | likely |

## Adding a rule

1. Pick a stable kebab-case ID.
2. Define severity, category, evidence, fix and confidence.
3. Add a fixture and a false-positive test.
4. Document whether it is source, live or manual.
5. Never emit a finding without a file/URL and evidence.
