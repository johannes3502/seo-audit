# Live rule catalog

Stable rule IDs for `seo_scan.py` (live crawl). `confirmed` = direct evidence;
`likely` = heuristic that must be verified. Severity is a triage default, not a
traffic estimate. Codebase rules are in `repo-rules.md`.

## Crawl and status

| ID | Severity | Evidence | Fix | Status |
|---|---|---|---|---|
| `fetch-error` | critical | exception, URL | DNS/TLS/firewall/URL prüfen | v0.2 |
| `http-status` | critical | status code | URL reparieren oder 301 auf gültiges Ziel | v0.2 |
| `redirect-chain` | high/medium | chain[] | einen 301 auf das Finalziel | v0.2 |
| `robots-unavailable` | medium | status, error | robots.txt mit Sitemap-Verweis ausliefern | v0.2 |
| `robots-blocks-start` | critical | robots.txt | Startseite freigeben | v0.2 |
| `robots-blocks-page` | high | URL, rule | Regel prüfen; nur blockieren, wenn gewollt | planned |
| `robots-no-sitemap` | low | robots.txt | absolute Sitemap-Zeile ergänzen | v0.2 |
| `noindex` | high/medium | meta robots, X-Robots-Tag | nur bei bewusstem Ausschluss | v0.2 |
| `canonical-missing` | medium | head | selbstreferenzierenden Canonical setzen | v0.2 |
| `canonical-mismatch` | medium | canonical vs. final | Canonical prüfen | v0.2 |
| `canonical-cross-host` | high | canonical host | eigene kanonische URL setzen | v0.2 |
| `sitemap-missing` | medium | sitemap status | XML-Sitemap erzeugen und verlinken | v0.2 |
| `sitemap-invalid` | high | parse error | valides XML, absolute URLs | v0.2 |
| `sitemap-start-missing` | medium | sitemap count | Startseite aufnehmen | v0.2 |
| `sitemap-noindex-urls` | medium | URL list | noindex-URLs aus der Sitemap entfernen | v0.2 |
| `hreflang-invalid` | medium | invalid codes | ISO 639-1 + optional ISO 3166-1 Alpha 2 | v0.2 |
| `hreflang-self-missing` | low | alternate links | Selbstverweis ergänzen | v0.2 |
| `soft-404` | high | unknown URL returns 200 | echten 404/410 liefern | v0.2 |
| `not-found-status` | medium | unknown URL status | Statuscode korrigieren | v0.2 |
| `not-found-unreachable` | medium | unknown URL error | Fehlerroute prüfen | v0.2 |

## Rendering

| ID | Severity | Evidence | Fix | Status |
|---|---|---|---|---|
| `csr-shell` | high | empty app mount, scripts | Public route server-render/prerender | v0.2 |
| `csr-thin-shell` | medium | <50 words, many scripts | Verify hydration; render content on server | v0.2 |
| `csr-only-app` | high/medium | framework/config | Add SSR/SSG or verify prerender output | repo |
| `csr-only-shell` | high/medium | index.html shell | Verify built HTML; otherwise prerender | repo |
| `client-page` | high | `"use client"` on route | Keep public content server-side | repo |
| `ssr-disabled` | high | `ssr: false` | Remove override for public routes | repo |
| `client-only-island` | medium | `client:only` | Server-render indexable content | repo |

## On-page

| ID | Severity | Evidence | Fix | Status |
|---|---|---|---|---|
| `title-missing` | high | head | eindeutigen Title setzen | v0.2 |
| `title-length` | low | title, length | 30–60 Zeichen, Keyword vorne | v0.2 |
| `title-duplicate` | high | title, URLs | pro Seite einzigartig | v0.2 |
| `description-missing` | medium | head | Description mit Nutzen und CTA | v0.2 |
| `description-length` | low | description, length | 70–160 Zeichen | v0.2 |
| `description-duplicate` | medium | description, URLs | pro Seite eigene Description | v0.2 |
| `h1-missing` | high | headings | genau eine inhaltliche H1 | v0.2 |
| `h1-multiple` | medium | headings | auf eine H1 reduzieren | v0.2 |
| `heading-order` | low | heading levels | Hierarchie lückenlos | v0.2 |
| `lang-missing` | low | html lang | `lang="de"` setzen | v0.2 |
| `lang-mismatch` | medium/info | html lang vs. `/de/` `/en/` | Sprache pro URL setzen (auch nach Hydration) | v0.2.4 |
| `host-alias-200` | medium | www/apex alias returns 200 without redirect | 301 auf kanonischen Host oder Canonical auf beiden Hosts | v0.2.4 |
| `viewport-missing` | high | meta viewport | Mobile-Viewport ergänzen | v0.2 |
| `og-missing` | low | meta og:* | OG-Tags ergänzen | v0.2 |
| `twitter-missing` | low | meta twitter:* | Twitter-Card ergänzen | v0.2 |

## Content

| ID | Severity | Evidence | Fix | Status |
|---|---|---|---|---|
| `thin-content` | medium/low | word count | Mehrwert ergänzen oder konsolidieren | v0.2 |
| `content-decay` | medium | GSC clicks trend | Inhalte aktualisieren/neu ausrichten | manual |
| `keyword-cannibalization` | high | query + multiple pages | eine Zielseite festlegen | manual |
| `ctr-gap` | medium | GSC CTR vs. position | Title/Description testen | manual |
| `eeat-signals` | medium | author, about, sources | Autoren-/Quellensignale ergänzen | manual |
| `duplicate-content` | high | text similarity | konsolidieren oder canonicalisieren | v0.2 |
| `near-duplicate-templates` | medium | template clusters | einzigartige Inhalte pro URL | v0.2 |

## Media

| ID | Severity | Evidence | Fix | Status |
|---|---|---|---|---|
| `images-alt-missing` | medium | count, URLs | sinnvolle alt-Texte | v0.2 |
| `images-dimensions-missing` | low | count | width/height/aspect-ratio | v0.2 |
| `image-format` | low | content-type, bytes | AVIF/WebP + srcset | v0.2 |
| `image-lazy-loading` | low | loading attr | below-fold lazy, LCP eager | v0.2 |

## Internal linking

| ID | Severity | Evidence | Fix | Status |
|---|---|---|---|---|
| `internal-links-none` | medium | link count | relevante interne Links | v0.2 |
| `orphan-page` | medium | inbound 0 | von relevanten Seiten verlinken | v0.2 |
| `broken-internal-link` | high | link, status | Link reparieren/entfernen | v0.2 |
| `redirect-internal-link` | medium | link, 301 | direkt auf Finalziel verlinken | v0.2 |
| `anchor-text-weak` | low | anchor text | beschreibende Ankertexte | manual |
| `link-depth` | medium | depth | wichtige Seiten ≤3 Klicks | manual |

## Performance

| ID | Severity | Evidence | Fix | Status |
|---|---|---|---|---|
| `slow-response` | low | TTFB ms | Hosting/Cache/DB prüfen | v0.2 |
| `html-size` | low | bytes | Markup reduzieren | v0.2 |
| `scripts-many` | low | count | Scripts entfernen/deferren | v0.2 |
| `render-blocking` | medium | PSI/Lighthouse | kritische CSS/JS optimieren | v0.2 |
| `lcp-slow` | high | PSI/CrUX LCP | LCP-Bild/Text priorisieren | v0.2 |
| `cls-high` | high | PSI/CrUX CLS | Dimensionen/Platzhalter | v0.2 |
| `inp-high` | high | PSI/CrUX INP | JS-Handling reduzieren | v0.2 |
| `field-vs-lab-gap` | medium | CrUX vs. Lighthouse | Felddaten priorisieren | manual |

## Mobile and accessibility

| ID | Severity | Evidence | Fix | Status |
|---|---|---|---|---|
| `mobile-overflow` | medium | viewport, scrollWidth | Layout Fix | v0.2 |
| `tap-target-small` | low | Lighthouse a11y | Ziele ≥24px | v0.2 |
| `color-contrast` | medium | Lighthouse a11y | Kontrast ≥4.5:1 | v0.2 |
| `focus-visible` | low | Lighthouse a11y | Fokus sichtbar | v0.2 |

## Structured data

| ID | Severity | Evidence | Fix | Status |
|---|---|---|---|---|
| `jsonld-missing` | low | types | passendes Schema ergänzen | v0.2 |
| `jsonld-invalid` | medium | parse errors | JSON syntaktisch korrigieren | v0.2 |
| `jsonld-mismatch` | high | visible text vs. schema | Schema = sichtbarer Inhalt | v0.2 |
| `schema-required-fields` | medium | type, missing fields | Pflichtfelder ergänzen | v0.2 |
| `faq-schema-mismatch` | high | questions vs. FAQ | nur sichtbare FAQs auszeichnen | v0.2 |

## Security and trust

| ID | Severity | Evidence | Fix | Status |
|---|---|---|---|---|
| `mixed-content` | high | http resources | HTTPS erzwingen | v0.2 |
| `security-headers` | medium/low | missing headers | HSTS, CSP, nosniff, Referrer-Policy | v0.2 |
| `https-missing` | critical | scheme | HTTPS + Redirect | v0.2 |
| `certificate-expiry` | high | TLS | Zertifikat erneuern | v0.2 |

## AI search readiness (GEO)

Google says AI Overviews/AI Mode need no special files or schema; normal SEO
applies. llms.txt is ignored by Google Search. AI-bot blocks are a business
choice, not a defect.

| ID | Severity | Evidence | Fix | Status |
|---|---|---|---|---|
| llms-txt-optional | info | status | only for non-Google agents, if useful | v0.2 |
| i-bot-blocked | info | robots group | only change if the business wants AI crawlers | v0.2 |
| nswer-first-content | medium | page text | answer the main question early | manual |
| citation-sources | medium | outbound links | source numbers and claims | manual |
| i-overview-presence | info | Search Console/SERP | observe, do not infer a penalty | manual |
| entity-consistency | medium | name/address/schema | keep NAP/entity consistent | manual |

## Reporting and operations

| ID | Severity | Evidence | Fix | Status |
|---|---|---|---|---|
| `gsc-access` | info | sites.list | Property-Zugriff klären | v0.2 |
| `gsc-quota` | info | API response | Sampling/Zeiträume anpassen | v0.2 |
| `crawl-budget-waste` | medium | URL patterns | Facetten/Parameter steuern | manual |
| `log-file-bot-mix` | info | server logs | echte Bot-Besuche prüfen | manual |
| `deploy-regression` | high | diff before/after | CI-Gate für SEO | manual |

## Adding a rule

1. Pick a stable ID (kebab-case, no version suffix).
2. Define severity, evidence fields and a concrete fix.
3. Add a fixture and a false-positive test.
4. Document whether it is `v0.1`, `v0.2` or `Pro`.
5. Never emit a finding without evidence.
