# Dogfood cases

These are anonymized real runs, not benchmarks. Page caps differ, so the scores
are triage signals, not a controlled comparison. No customer names, domains or
private data are included.

## 1. SaaS marketing site — live scan

```bash
python "$SKILL/scripts/seo_scan.py" https://example-saas.com \
  --max-pages 10 --max-depth 2 --timeout 20 --out live-saas
```

- **Score:** 84/100
- **Pages:** 10/10 (page cap reached; sample, not full inventory)
- **Findings:** 0 critical, 0 high, 0 medium, 16 low
- **Main lows:** TTFB around 1.9–2.1 s, four descriptions at 186–195
  characters, one image without dimensions, one title at 66 characters.
- **Good signals:** every crawled route had a title, description, one H1,
  canonical and JSON-LD; no missing alt text; no mixed content; no CSR shell in
  the raw HTML.

Lesson: a healthy marketing site still produces a long low-severity list. That
is not a reason to rewrite it.

## 2. Hospitality site — negative control

```bash
python "$SKILL/scripts/seo_scan.py" https://example-hospitality.com \
  --max-pages 2 --max-depth 1 --timeout 20 --out live-control
```

- **Score:** 65/100
- **Pages:** 2/2 (page cap reached; `/cart` is skipped)
- **Findings:** 0 critical, 3 high, 3 medium, 14 low
- **High:** mixed content (an HTTP image on HTTPS), duplicate title on both
  crawled pages.
- **Medium:** duplicate description, one page with no incoming internal link in
  the sample, start URL missing from the sitemap.
- **Low:** 900 KB HTML, 34 script tags, 4 images without dimensions, missing
  security headers, ~1.9 s TTFB, 290 words, 14-character title.

The lower score is expected. It is still a two-page sample; do not treat it as
a full-site verdict.

## 3. Vite site with a prerender step — source scan + live confirmation

```bash
python "$SKILL/scripts/repo_scan.py" apps/web --out repo-web
```

- **Detected:** Vite SPA with a hybrid/prerender configuration, 21 routes from
  the React Router config.
- **Code findings:** 41 (15 medium, 26 low). The source `index.html` is an app
  shell; 16 page files have no H1 in the page file (the H1 lives in imported
  components); 7 first images are lazy-loaded; 3 anchors have no crawlable
  destination; 2 images lack alt text; CSS uses `@import`; no sitemap file or
  generator lives inside this subdirectory (the generator lives one level
  above).
- **Live confirmation:** the crawled routes do contain title, H1, text,
  canonical and JSON-LD, so the built output is prerendered. The source-shell
  finding is a lead, not a defect.
- **Lesson:** when a Vite/React source is a shell but a prerender step exists,
  verify the built HTML. Component-rendered H1s and below-the-fold images need
  a rendered check. Run the scanner with the build context if generators live
  outside the app folder.

## 4. Next.js App Router export + FastAPI backend — monitored agent run

An agent ran the skill in review mode on a Next.js 16 App Router static export,
a FastAPI backend and two live domains.

- **Before the 0.2.1 fixes:** the scanner called the Next app "Pages Router",
  found 0 routes, reported a route-group layout as `global-noindex` (critical),
  missed `src/app/robots.ts`, flagged the built-in 404, and turned email
  templates, admin shells and a served frontend export into 27 "routes"
  (backend score 24/100). The agent had to correct all of these manually.
- **After the fixes:** `src/app` is detected, 11 routes, the nested layout is
  scoped, metadata routes and the default 404 are recognized, inherited
  metadata is `info`, and the static export downgrades `"use client"` to
  `info`. Backend: FastAPI, 0 routes, 100/100. Frontend: 90/100, 20 findings,
  1 medium (`hreflang-missing` for client-only EN switching).
- **Live:** the crawl reports its coverage (1 sitemap URL, 3 pages), legal
  `noindex` is `info`, expired Event JSON-LD is medium, and the www/non-www
  split between canonical, sitemap and final host is reported.
- **Lesson:** the agent's verification step caught every false positive, but
  fixing the framework adapter and the scope rules removed the noise at the
  source. A single recursive file listing over build output flooded the
  context; the skill now warns against it.

## 5. Umbrella repository — scope instead of a score

A root with submodules, several frontends, backends, a docs folder and a local
preview tool produced a 0/100 site score and 174 mixed findings before 0.2.4.

- **After the scope rules:** the root is `umbrella` with no score. Each public
  app root is scanned separately, internal apps are checked only for accidental
  indexability, docs are read as context, and local tools are classified as
  non-public.
- **Lesson:** an umbrella root is not a website. Report the inventory, not a
  score.

## What these cases do not prove

- They do not prove indexing or ranking.
- They do not compare two sites fairly (different page caps).
- They do not replace field Core Web Vitals or Search Console data.
- They do not validate every framework edge case; the unit tests cover the
  scanner contracts, not a customer's app.
