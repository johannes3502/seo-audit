# Framework-specific SEO map

Use this to find the right file, not as a substitute for reading the actual
repository. Framework APIs change; verify the installed version.

## Next.js App Router

| Concern | Where |
|---|---|
| Per-route title/description/canonical/robots/OG | `export const metadata` or `generateMetadata` in `page.tsx`/`layout.tsx` (Server Components) |
| Shared metadata | root `app/layout.tsx`, `metadataBase`, title template |
| Sitemap | `app/sitemap.ts` (`MetadataRoute.Sitemap`) |
| robots.txt | `app/robots.ts` (`MetadataRoute.Robots`) |
| 404 | `app/not-found.tsx`; `notFound()` from a server component |
| Redirects | `next.config.*` `redirects()` or route handlers |
| Images | `next/image`; set `sizes`, dimensions/`fill`; `priority` only for LCP |
| Client boundary | `"use client"` at the top of a file; keep public content server-side |

Pitfalls: page-level `openGraph` replaces rather than merges; a `noindex` in a
layout removes every child route; `generateMetadata` can stream, but critical
tags should be in the initial HTML for non-JS crawlers.

## Next.js Pages Router

| Concern | Where |
|---|---|
| Head tags | `next/head` / a head component |
| Sitemap | `public/sitemap.xml` or `next-sitemap` |
| robots.txt | `public/robots.txt` |
| 404 | `pages/404.tsx` |
| Redirects | `next.config.*` or `getServerSideProps` |

## Nuxt

| Concern | Where |
|---|---|
| Per-page meta | `useSeoMeta({...})` or `useHead({...})` |
| Global defaults | `app.head` in `nuxt.config.*`, `app.vue` |
| Sitemap | `@nuxtjs/sitemap` module |
| robots.txt | `nuxt-robots` module or `public/robots.txt` |
| 404 | `error.vue`; `createError({ statusCode: 404 })` |
| Rendering | `ssr: false` in config or route rules turns SSR off |

Pitfalls: `useSeoMeta` can be reactive, but static tags can be server-only for
performance; verify the built HTML, not only the dev overlay.

## SvelteKit

| Concern | Where |
|---|---|
| Head tags | `<svelte:head>` in `+page.svelte`/`+layout.svelte` |
| SSR control | `export const ssr = false` in `+page.js`/`+layout.js` |
| Prerender | `export const prerender = true`; `entries()` for dynamic routes |
| Sitemap | `src/routes/sitemap.xml/+server.ts` or prerender step |
| 404 | `+error.svelte`; `error(404, 'Not found')` |
| Redirects | `redirect(301, ...)` from load |

Pitfalls: `ssr = false` creates an empty shell; data that only loads in
`onMount` is not in the initial HTML; canonical built from `window.location` is
missing on the server.

## Astro

| Concern | Where |
|---|---|
| Head tags | one layout with `<title>`, description, canonical, OG |
| Site URL | `site` in `astro.config.*` |
| Sitemap | `@astrojs/sitemap` integration |
| robots.txt | `src/pages/robots.txt.ts` or `public/robots.txt` |
| 404 | `src/pages/404.astro` |
| Rendering | static output by default; `client:only` skips server HTML |

Pitfalls: `client:only` around the main content; dynamic routes in SSR mode need
a sitemap strategy; `site` missing breaks canonical/sitemap URLs.

## Remix / React Router

| Concern | Where |
|---|---|
| Per-route meta | `export const meta`/`export function meta` (or React 19 `<title>`/`<meta>`) |
| Root document | `app/root.tsx` with `<Meta />` in `<head>` |
| 404 | throw a `Response` with status 404 from a loader |
| Headers | `headers` export (`X-Robots-Tag`, cache) |
| Sitemap | resource route or build script |
| Links | `<Link>` renders a real `<a href>` |

Pitfalls: nested `meta` is replaced, not merged; a client-only loader can leave
content out of the server HTML; a catch-all route can create soft 404s.

## Vite / React / Vue SPA

| Concern | Where |
|---|---|
| Shell | `index.html` with `<div id="root"></div>` |
| Routes | client router (`react-router`, `vue-router`) |
| Metadata | client head library (`react-helmet`, `@unhead/vue`) |
| Sitemap/robots | `public/` or a build script |

For public content, this is the highest-risk setup. Prefer SSR/SSG (Next.js,
Nuxt, SvelteKit, Astro) or a prerender step that writes complete HTML for each
public route. Keep CSR for authenticated app screens.

## Django / Flask / FastAPI templates

| Concern | Where |
|---|---|
| Base template | `templates/base.html` with title block, description, canonical |
| Per-page meta | template blocks / context variables |
| Sitemap | `django.contrib.sitemaps`, a Flask/FastAPI route, or a static file |
| robots.txt | static file or route |
| 404 | `404.html` + a handler that returns 404 |
| Redirects | URL config / view redirects |

Pitfalls: one global title in the base template; canonical hardcoded to the
homepage; error pages returning 200; missing `lang` attribute.

## Rails

| Concern | Where |
|---|---|
| Layout | `app/views/layouts/application.html.erb` |
| Per-page meta | `content_for :title`, `content_for :meta_description` |
| Sitemap | `sitemap_generator` gem or a route |
| robots.txt | `public/robots.txt` |
| 404 | `public/404.html` + `config.exceptions_app` |

## WordPress

| Concern | Where |
|---|---|
| Head | `wp_head()`, theme templates, SEO plugin |
| Sitemap | core `/wp-sitemap.xml` or plugin |
| robots.txt | virtual `robots.txt` or `robots_txt` filter |
| 404 | `404.php` |
| Canonical | `rel_canonical()` / plugin |

Pitfalls: plugin and theme both output meta tags; staging site indexed; page
builder content not in the initial HTML; duplicate canonical tags.
