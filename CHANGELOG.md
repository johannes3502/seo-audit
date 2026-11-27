# Changelog

## 0.4.0 — 2026-11-27

Feedback-driven audit expansion: local business/entity, trust/legal and event
eligibility, plus measurement and evidence discipline.

- **Local business and entity coverage**: new `references/checklists/local.md`
  (NAP, GBP, LocalBusiness schema, location/service pages, reviews, citations,
  events) and `references/checklists/trust.md` (imprint, privacy, terms,
  contact, cross-domain legal links).
- **Research gate and coverage ledger**: the agent must read the matching
  checklist and state which references were used, which areas were checked and
  what was not checked.
- **Measurement contract**: page cap, depth, date, static HTML vs rendered DOM,
  per-URL word/script counts and no cross-scope score comparisons.
- **Live rules**: `event-not-leaf-page`, `event-fields-missing`,
  `event-organizer-cross-host`, `localbusiness-nap-incomplete`,
  `localbusiness-telephone-missing`, `localbusiness-hours-missing`,
  `localbusiness-address-not-visible`, `localbusiness-sameas-missing`,
  `legal-link-cross-domain`, `og-locale-alternate-without-url`,
  `landmark-nesting`, `sitemap-robots-conflict`, `index-html-duplicate`.
- **Source rules**: `canonical-shared`, `sitemap-lastmod-build-time`,
  `robots-blocks-noindex`, `robots-blocks-public-route`, `client-only-i18n`,
  `schema-event-fields`, `schema-event-list`,
  `schema-localbusiness-recommended`.
- **False-positive fix**: a client-only language switch with locale files but
  no locale URLs is `client-only-i18n` (info), not `hreflang-missing`.
- **Docs**: new checklists, report template coverage ledger, local/trust/event
  sections, README feature list, rule catalogs and eval prompts.
- 36 tests pass; validator and compile checks pass.

## 0.3.1 — 2026-11-26

- Fixed UTF-8 text that had been double-encoded in `SKILL.md`, the example
  report and the GSC reference. No scanner or rule behavior changed.
- Crawler user agent now identifies itself as `seo-audit/0.3.1`.

## 0.3.0 — 2026-11-26

First public release as a single-skill repository. No behaviour change in the
scanners beyond the cleanup below.

- **Repository shape**: `SKILL.md` now lives at the repository root, so the repo
  can be cloned directly into a skills directory (`seo-audit`). One skill, one
  repository, no nested `skills/` folder.
- **Public identity**: README rewritten around what the skill does, who it is
  for, how it works, what it does not do, and how to verify it. Added
  `AGENTS.md`, `PUBLISHING.md`, `CODE_OF_CONDUCT.md`, issue/PR templates and a
  CI matrix on Python 3.10 and 3.12.
- **No project artifacts**: removed every project- and customer-specific name,
  domain, example keyword and internal route from the skill, tests, changelog,
  credits and cases. Dogfood cases are anonymized.
- **Neutral defaults**: the crawler user agent and internal route segments are
  generic; examples use a project-management keyword map and `apps/`,
  `services/`, `docs/` and `tools/preview/`.
- **Package hygiene**: fixed mixed-encoding text in the credits and the sample
  report, corrected a sample recommendation that contradicted the embedded
  research, and updated the copyright holder.
- 24 tests pass; validator and compile checks pass.

## 0.2.4 — 2026-11-26

Fixes from a monitored run on a large umbrella repository (several public apps,
a docs workspace, a local tool, internal dashboards and multiple domains).

- **Scope-first inventory**: `repo_scan.py` detects `.gitmodules`, app roots and
  docs/local tools, returns `project.app_type`, `project.apps` and no site score
  for `umbrella`, `docs`, `local-tool`, `backend`, `internal` and `context`
  roots. The umbrella root no longer produces 0/100 and 174 mixed findings.
- **No more silent ignoring**: a docs/context workspace is inventoried with its
  TODO/strategy sources, a local tool is classified as `local-tool`, and
  internal apps are marked `internal` instead of receiving marketing scores.
- **UTF-16 input**: `requirements.txt` and config files written as UTF-16 are
  decoded correctly; FastAPI services are no longer "Unknown".
- **Router adapters**: `createBrowserRouter`/`useRoutes` object configs,
  `basename` prefixes and locale siblings (`/de/…` and `/en/…`) are extracted.
  A 17-route app no longer shows 2 routes; an internal app no longer shows 0.
- **Runtime metadata and Hero components**: `useMeta`/Helmet/`useHead` with
  variables and an imported `*Hero` component are `info`, not missing
  title/description/H1. A website no longer produces 16 false H1 findings.
- **Sitemap context**: generators and route registries one level above the app
  root are found; `sitemap-missing` and `csr-only` false positives are gone.
  Sitemap-only hreflang is `low`, not medium.
- **Built output**: `dist/` awareness plus `--include-dist`; scanning a built
  folder now works as static evidence, and a built SPA shell is still
  `csr-only-shell`.
- **Live scanner**: noindex app/auth pages no longer get high H1/canonical/
  internal-link findings; CSR symptoms are `info` under one `csr-shell` root
  cause; `lang-mismatch` catches `/en/` with `lang="de"`; `host-alias-200`
  catches a `www` duplicate without redirect; `draft-indexable` ignores product
  terms and requires low content/placeholder context.
- **CLI**: `--scope auto|public|internal|context`, `--include-dist`.
- 24 tests pass, including UTF-16 FastAPI, umbrella inventory, createBrowserRouter,
  locale siblings, runtime metadata, product-term draft markers and host alias.

## 0.2.3 — 2026-11-26

Fixes from a monitored run on an Astro monorepo.

- **Monorepo scope warning**: a root scan with several `package.json` files and
  0 routes now emits `scan-scope` and a `SCOPE WARNING` in the verdict, instead
  of a misleading 97/100.
- **Draft detection**: indexable pages with draft/placeholder markers
  ("Entwurf", "Platzhalter", "in Arbeit", "TODO") are flagged as
  `draft-indexable` (low) in source and live scans.
- **Bundled CSS**: source `@import` is `info`, not `low`, for frameworks whose
  bundler inlines it (Next, Nuxt, SvelteKit, Astro, Remix, Vite, Angular).
- **Multi-host crawl**: `seo_scan --include-host app.example.com` crawls an app
  or add-in origin (root is seeded, links are followed, robots still applies)
  and reports it in coverage. Cross-host orphan pages are not flagged.
- **Canonical target check**: `canonical-target-status` and
  `canonical-target-redirect` verify that the canonical resolves to 200 and not
  through a redirect; a canonical to a 404 is caught.
- **Fetch errors**: a timeout on a linked page is `medium` with a retry note;
  only a failure of the start URL is `critical`. Linked 4xx pages are `high`,
  not `critical`.
- `repo_scan`: dynamic `href={...}` is not a broken link; Astro metadata passed
  as props stays `info`; `routes.csv` remains a real inventory.

## 0.2.2 — 2026-11-26

Fixes from a monitored run on an Astro static site.

- **Astro dynamic metadata**: a page that passes `title={...}` or
  `description={...}` to a layout is no longer `medium`; the finding is `info`
  with a note to verify the built HTML. Literal layout props are still read.
- **Astro anchors**: `<a href={...}>` is not flagged as `link-not-crawlable`
  anymore; only truly empty/`#`/`javascript:` targets are.
- **Legal pages**: `thin-content` is `info` for AGB, AVV, Datenschutz,
  Impressum, Cookies, Widerruf and similar pages; the pattern now includes
  `avv` and `nutzungsbedingungen`.
- Result on a 25-route frontend: 43/100 → 90/100; the live report 71 → 77 with
  no medium thin-content on legal pages.

## 0.2.1 — 2026-11-25

Fixes from a monitored real-world run on a Next.js App Router export plus a
FastAPI backend.

- **Next.js App Router detection** now sees `src/app/**/page|layout|route` and
  no longer falls back to Pages Router, which had produced 0 routes and
  cascading keyword false positives.
- **Scoped layouts**: only the root layout is treated as global. Nested and
  route-group layouts (`(marketing)/layout.tsx`) no longer emit
  `global-noindex`.
- **Metadata routes**: `app/robots.ts`, `app/sitemap.ts` and built-in 404s are
  recognized; no more `robots-missing` or `not-found-missing` for them.
- **Inherited metadata**: missing title/description on a Next page that has a
  root layout default is `info`, with a note to verify the built HTML.
- **Static export**: `"use client"` plus `output: "export"` is `info`, not
  `high`; a client page can still be prerendered.
- **Private routes**: account, login, admin, preview, confirm, unsubscribe and
  email templates are not counted as marketing pages; email templates are no
  longer routes.
- **Python backends**: `src/pyproject.toml`/requirements are read; FastAPI and
  Django are detected before static HTML, so admin shells do not become routes.
- **Canonical checks**: www/non-www mismatch between canonical and final URL is
  reported (`canonical-host-alias`); the sitemap and robots `Sitemap:` host are
  compared too (`sitemap-host-alias`, `sitemap-cross-host`).
- **Legal noindex**: `agb`, `datenschutz`, `imprint` etc. are `info`, not
  `medium`, because the policy is usually intentional.
- **Event freshness**: JSON-LD `Event` nodes with a past `endDate` still marked
  `EventScheduled` are flagged (`jsonld-event-expired`).
- **Coverage**: live report states crawled pages vs sitemap URLs and explains
  when the crawl is complete.
- **TTFB**: a single slow sample is labeled as one measurement, not a defect.
- New flags: `repo_scan --exclude` and `seo_scan --include-url`.
- `routes.csv` is now a real route inventory; findings moved to `issues.csv`.
- SKILL.md: script paths are resolved from the skill folder (global installs),
  plus a known-heuristic section, Windows-safe file enumeration and extended
  failure modes.

## 0.2.0 — 2026-11-25

- **Generalized the skill.** An early project-specific `--profile` and its rule
  file were removed. The skill applies to any repository and any public domain.
- Added `repo_scan.py`: dependency-free source scanner for framework,
  rendering model, routes, metadata, SSR/CSR risks, indexing, sitemap/robots,
  404/soft-404, images, links, JSON-LD, hreflang and keyword coverage.
- Added review/apply workflow: review is the default; full optimization only
  after the user selects batches.
- Added permanent research references (`references/research/`) and checklists
  (`references/checklists/`) covering Google Search Essentials, SSR/rendering,
  indexing, keyword optimization, E-E-A-T, Core Web Vitals, structured data,
  internationalization, AI search, framework maps and measurement.
- Corrected AI-search guidance: `llms.txt` is ignored by Google Search; no
  special schema/file is required for AI Overviews/AI Mode.
- Added general live checks: CSR shell, soft 404, hreflang validity, sitemap
  noindex conflicts, `robots` sitemap line.
- Added `tests/test_repo_scan.py` and a CSR fixture; updated the live scanner
  tests.
- Added `plans/2026-11-25-requirements.md` with unambiguous requirements and
  acceptance criteria (internal, not part of the public repository).
- README rewritten as a developer tool, not a hosted product.

## 0.1.0 — 2026-11-20

- Initial `seo-audit` skill.
- Dependency-free static scanner with JSON/Markdown/CSV output.
- ~70 deterministic checks: crawl, indexing, on-page, media, internal links,
  performance basics, security headers, AI-search readiness.
- Optional read-only GSC quick-wins script.
- Rule catalog, report template and GSC limits.
- Evals, validator, unit tests and a GitHub Actions workflow.
- Product plan, market research, skill best practices and decision log
  (internal, not part of the public repository).
