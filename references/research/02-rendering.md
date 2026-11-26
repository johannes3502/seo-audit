# Rendering and SSR for SEO

Sources: Google JavaScript SEO basics, Dynamic rendering, Rendering for
content-driven apps; Next.js, Nuxt, SvelteKit, Astro and Remix docs (see
`00-sources.md`).

## The pipeline

Google crawls the URL, parses the returned HTML for links, then may queue the
page for rendering in a browser-like environment. Indexing uses the rendered
result when rendering is needed. This creates three risks:

1. **The initial HTML is empty** (CSR shell). Google may render it, but other
   crawlers and AI agents often do not run JavaScript.
2. **The rendered HTML differs from the initial HTML** (metadata rewritten,
   canonical changed, `noindex` added/removed, hydration error). Google may see
   a different page than the user.
3. **The page is slow or fragile** because content waits for a bundle, an API
   call and hydration. That hurts LCP/INP and makes indexing less reliable.

Google says server-side rendering, static rendering or hydration are the
recommended solutions. Dynamic rendering is documented as a workaround, not a
long-term solution.

## Rendering modes

| Mode | Initial HTML | SEO risk | Typical use |
|---|---|---|---|
| SSR | Full HTML per request | Low if stable and fast | Personalized or frequently changing public pages |
| SSG | Full HTML at build time | Lowest | Marketing, docs, blogs, product pages |
| ISR / incremental | Full HTML, refreshed later | Low | Large catalogs, news |
| Hybrid | Per-route choice | Low when public routes are server-rendered | Most modern apps |
| CSR | Shell + scripts | High for public content | Logged-in tools, dashboards |
| Islands | Static HTML + selective hydration | Low | Astro-style content sites |
| Dynamic rendering | Bot-specific HTML | Medium; two versions can drift | Legacy CSR stopgap only |

## What must be in the initial HTML

For every public, indexable route:

- unique `<title>`
- meta description (not a ranking factor, but a snippet input)
- canonical URL (ideally in the raw HTML; do not change it later with JS)
- robots directives (`noindex` must be visible without JS)
- one meaningful H1
- primary body text
- crawlable `<a href>` links to important pages
- language and viewport metadata
- structured data that describes visible content
- image `alt` and dimensions for the primary images

## Common SSR/CSR bugs to look for

- `"use client"` on a Next.js page that owns public content.
- `ssr: false` in Next.js dynamic imports or Nuxt config.
- `export const ssr = false` in SvelteKit `+layout`/`+page`.
- Astro `client:only` around the main content.
- Vite/React `index.html` with `<div id="root"></div>` and all content in JS.
- Data fetched in `useEffect`/`onMount` instead of a server loader.
- `window`/`document` accessed at module scope, forcing client-only rendering.
- A spinner or skeleton as the only server HTML.
- A catch-all server rewrite to `index.html` (soft 404 factory).
- Metadata set only via `document.title` or a client-side head library.
- A `noindex` that JavaScript removes: Google may never render it to see the
  removal.
- A canonical that JavaScript changes to a different URL than the raw HTML.

## Framework map

### Next.js App Router

- `export const metadata` or `generateMetadata` in a Server Component.
- `app/sitemap.ts`, `app/robots.ts`, `app/not-found.tsx`.
- `metadataBase` and a title template in the root layout.
- Page-level `openGraph` replaces the parent object rather than merging.
- `generateMetadata` can stream; crawlers that do not run JS need the tags in
  the initial HTML, so keep critical metadata resolvable on the server.

### Next.js Pages Router

- `next/head` or a head component; ensure tags are in the server response.
- `public/sitemap.xml` or `next-sitemap`; `public/robots.txt`.
- `pages/404.tsx` for a real 404.

### Nuxt

- `useSeoMeta` (typed) or `useHead`; `app.head` for static defaults.
- `useSeoMeta` should be server-rendered for crawlers; Nuxt docs note robots
  primarily scan the initial page load.
- `@nuxtjs/sitemap` and `nuxt-robots` are common; verify the generated files.

### SvelteKit

- SSR is the default; `export const ssr = false` creates an empty shell.
- `<svelte:head>` for title/description/canonical; return SEO data from a
  server `load`.
- `src/routes/sitemap.xml/+server.ts` or a prerender step.
- `+error.svelte` for errors; ensure the response status is 404.

### Astro

- Static output by default; `client:only` skips server rendering.
- Set `site` in `astro.config.*`; `@astrojs/sitemap` for sitemaps.
- Put metadata in one layout; avoid duplicating `<title>` in pages.

### Remix / React Router

- Route `meta` export (or React 19 `<title>`/`<meta>` elements).
- `loader` returns data and real 404s; `headers` can set `X-Robots-Tag`.
- Root route renders `<Meta />` inside `<head>`.
- Nested routes: the leaf `meta` replaces parent meta unless merged.

## Verification

1. `curl -sL URL | head` or `view-source:`: is the title/H1/text/canonical in
   the raw HTML?
2. Disable JavaScript in the browser: is the primary content still there?
3. Compare raw vs rendered DOM (DevTools or a headless browser).
4. Check status codes for unknown paths; a SPA fallback that returns 200 is a
   soft 404.
5. Test a direct request, not only client-side navigation.
6. Use Search Console URL Inspection for the live rendered page when available.
