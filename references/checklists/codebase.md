# Codebase SEO checklist

Use this after `repo_scan.py`, before editing. Mark each item `confirmed`,
`likely`, `hypothesis` or `not applicable`.

## 0. Scan safety

- [ ] The scan root is a single app, not an umbrella/submodule root; if the
      scanner returns `app_type=umbrella`, use `project.apps` and scan each app.
- [ ] Public, internal, mixed, docs/context, local-tool and backend surfaces
      are classified before applying SEO rules.
- [ ] Internal apps (`noindex,nofollow`, `Disallow: /`, `X-Robots-Tag`) are
      checked only for accidental indexability; they get no marketing score.
- [ ] Mixed hosts: a public SSR route (for example `/t/<slug>`) is reconciled
      with the host's robots/meta/canonical policy.
- [ ] Docs/context repos (`business/`, `docs/`, `marketing/`) are read for
      intent/strategy, not scanned as web routes.
- [ ] A local-only tool (README binds to `127.0.0.1`) is not scored as a site.
- [ ] Built output is checked when the source is a shell (`dist/`, `out/`,
      `.next/`); for SPAs the served HTML is the evidence.
- [ ] Sitemap/prerender generators outside the app root (`../scripts`,
      root `package.json` scripts) are found before `sitemap-missing` is reported.
- [ ] Framework label is correct (Next App Router under `src/app` is not Pages
      Router); 0 routes while routes exist means the scan root is wrong.
- [ ] Route groups `(marketing)` are treated as scoped, not global.
- [ ] `app/robots.ts`, `app/sitemap.ts`, `app/manifest.ts` and `not-found.*`
      are recognized as metadata routes.
- [ ] A page without its own title may inherit the root layout; verify the
      built HTML before reporting it as missing.
- [ ] Runtime metadata hooks (`useMeta`, Helmet, `useHead`) and Hero components
      are sources of truth; missing literals in the page file are `info`.
- [ ] Private/app routes (account, login, admin, preview, email templates) are
      not counted as marketing pages.
- [ ] File listing stayed inside source folders; build output (`out/`, `.next/`,
      `dist/`, `node_modules/`, `map-data/`) was never recursed.
- [ ] Suspected encoding damage was checked on the bytes, not only in the
      console (`Get-Content -Encoding UTF8` / Python UTF-8 decode). UTF-16
      `requirements.txt` is decoded correctly.

## 1. Project and rendering

- [ ] Framework and version identified (Next/Nuxt/SvelteKit/Astro/Remix/Vite/
      Angular/Django/Flask/FastAPI/Rails/WordPress/static).
- [ ] Rendering mode per public route: SSR, SSG, ISR, hybrid, CSR, islands.
- [ ] Public money pages are not client-only.
- [ ] No `ssr: false` / `"use client"` / `client:only` around the primary
      content of a public page.
- [ ] A build/prerender step exists if the source is a Vite/React/Vue SPA.
- [ ] Raw HTML (built output) contains title, H1, primary text and links.
- [ ] Hydration does not replace or remove the server-rendered content.

## 2. Routes and metadata

- [ ] Each public route has a unique title.
- [ ] Titles are descriptive and not generic templates.
- [ ] Each money page has a unique meta description.
- [ ] Canonical is self-referential and generated per route.
- [ ] A shared layout does not hardcode one canonical or one title.
- [ ] Root-layout defaults are overridden by every indexable route.
- [ ] `noindex` is not applied to the shared layout by accident; scoped
      `noindex` in a section/route-group layout is intentional.
- [ ] Legal pages that are `noindex` are also excluded from the sitemap.
- [ ] 404 route returns a real 404 status; frameworks with a built-in 404 do
      not need a custom file.
- [ ] Unknown paths do not fall back to a 200 `index.html`.
- [ ] Pagination/facets have a deliberate indexation strategy.

## 3. Crawling

- [ ] `robots.txt` allows the public site and needed assets.
- [ ] `robots.txt` references an absolute sitemap URL.
- [ ] Sitemap generator exists and includes canonical, indexable URLs.
- [ ] `noindex` URLs are excluded from the sitemap.
- [ ] Redirects are server-side 301/308, no chains.
- [ ] HTTP → HTTPS and www/non-www canonicalization is deliberate.
- [ ] Canonical, sitemap URLs and robots `Sitemap:` line use the same final
      host; none of them points at a host that 301s elsewhere.
- [ ] CDN/firewall does not block Googlebot or required assets.
- [ ] No two public routes share one hardcoded canonical.
- [ ] `Disallow` paths are not public routes and do not hide a `noindex`.
- [ ] Sitemap `lastmod` is the content modification date, not the build time.
- [ ] Sitemap URLs are crawlable (no `robots.txt` conflict).

## 4. Content and keywords

- [ ] A keyword map exists for priority routes (URL → primary intent).
- [ ] One owner URL per intent; no cannibalization.
- [ ] Primary phrase appears naturally in title, H1 and opening copy.
- [ ] H1 is unique and matches the page topic.
- [ ] Heading outline is logical (H1 → H2 → H3).
- [ ] No keyword stuffing; no scaled thin pages.
- [ ] Internal links use descriptive anchors and real `<a href>`.
- [ ] Important pages are not orphans.
- [ ] Content has a clear next step (conversion path).

## 5. Media

- [ ] Informative images have alt text; decorative images use `alt=""`.
- [ ] Images have width/height or aspect ratio.
- [ ] Hero/LCP image is not lazy-loaded.
- [ ] Responsive images use `srcset`/`sizes` where appropriate.
- [ ] Modern formats (AVIF/WebP) with fallbacks.
- [ ] Images sit near relevant text and have descriptive filenames.

## 6. Structured data

- [ ] JSON-LD is valid JSON.
- [ ] The type matches the page (Organization, LocalBusiness, Article,
      Product, FAQPage, BreadcrumbList).
- [ ] Required fields for the chosen type are present.
- [ ] Markup values match visible content (price, availability, reviews, FAQ).
- [ ] Event markup is fresh: past `endDate` is not still `EventScheduled`.
- [ ] Event markup is a single event on its own leaf URL, not a homepage/list
      `ItemList`; `name`, `startDate`, `location` and organizer are real.
- [ ] `LocalBusiness` has name, address, telephone, hours and `sameAs`, matching
      the visible NAP and legal entity; no blanket 24/7 claim.
- [ ] No fake reviews/ratings or fabricated author data.
- [ ] Structured data is present on mobile and desktop.

## 7. Internationalization

- [ ] `lang` matches the page.
- [ ] Each locale has a stable URL.
- [ ] A client-side language switch without its own URL does not count as a
      second locale; either add URLs/hreflang or document the choice.
- [ ] hreflang cluster includes self-reference and return links.
- [ ] `x-default` points to a sensible fallback.
- [ ] canonical is self-referential per locale.
- [ ] No language redirect that hides variants from crawlers.

## 8. Performance

- [ ] LCP element identified; not lazy; optimized format/size.
- [ ] No unnecessary render-blocking CSS; no long `@import` chains.
- [ ] Non-critical JS deferred/async; bundle work reduced.
- [ ] Fonts self-hosted or preloaded; `font-display` set.
- [ ] Images/video reserve space (CLS).
- [ ] TTFB/caching/compression checked at the server/CDN.
- [ ] Field CWV measured, not only Lighthouse.

## 9. Measurement

- [ ] GSC property verified and accessible (optional).
- [ ] Baseline URLs, date range and metrics recorded.
- [ ] Build/test commands known.
- [ ] Post-change verification: build, tests, re-scan, deploy, compare.
