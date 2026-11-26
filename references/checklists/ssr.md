# SSR / rendering review checklist

Use this when the site must rank and the source looks like a client-rendered app.

## Evidence

- [ ] Fetch the URL with `curl` or `view-source` and save the raw HTML.
- [ ] Compare raw HTML with the rendered DOM.
- [ ] Disable JavaScript and reload.
- [ ] Check the route directly, not only via client-side navigation.
- [ ] Check the built output (`dist/`, `.next/`, `.output/`, `build/`), not
      only the source shell.

## For each public route

- [ ] Title, description, canonical, robots meta in raw HTML.
- [ ] H1 and primary text in raw HTML.
- [ ] Internal links in raw HTML.
- [ ] JSON-LD in raw HTML.
- [ ] Images in raw HTML with alt/dimensions.
- [ ] No loading spinner/skeleton as the only server output.
- [ ] No hydration mismatch that replaces content.
- [ ] No `noindex` that relies on JS to remove it.
- [ ] No canonical that JS changes to a different URL.

## Rendering controls

- [ ] Next: no `"use client"` on the page; no `ssr: false` dynamic import;
      metadata in Server Components.
- [ ] Nuxt: `ssr` not disabled for public routes; `useSeoMeta` server-rendered.
- [ ] SvelteKit: no `export const ssr = false` on public routes; SEO data from
      server load; `<svelte:head>` in the raw HTML.
- [ ] Astro: no `client:only` around the main content; `site` configured.
- [ ] Remix/React Router: `meta` export and server loader; `<Meta />` in root.
- [ ] Vite/Angular SPA: prerender/SSR step exists; built HTML verified.

## Framework-specific pitfalls

- [ ] Next: `openGraph` replacement vs merge; layout `noindex` inheritance;
      streaming metadata for non-JS crawlers.
- [ ] Nuxt: `app.head` static defaults vs per-page meta.
- [ ] SvelteKit: canonical from `window.location` is missing on the server.
- [ ] Astro: sitemap cannot enumerate dynamic SSR routes by default.
- [ ] Remix: nested `meta` replaces parent meta; leaf 404 status.
- [ ] SPA: catch-all rewrite creates soft 404s.

## Fix pattern

1. Move primary content into a server-rendered route/component.
2. Generate metadata from server data (same data as the page).
3. Render canonical from the request host/path, not a hardcoded constant.
4. Keep client components for interaction only.
5. Add a real 404 for unknown paths.
6. Verify raw HTML before and after.
