# Performance and Core Web Vitals

Sources: web.dev Web Vitals, LCP, INP, CLS, threshold methodology; Google Core
Web Vitals and page experience docs (see `00-sources.md`).

## Thresholds

Field data at the 75th percentile, mobile and desktop separately:

| Metric | Good | Poor | What it measures |
|---|---:|---:|---|
| LCP | ≤ 2.5 s | > 4.0 s | loading of the largest visible element |
| INP | ≤ 200 ms | > 500 ms | responsiveness to interactions |
| CLS | ≤ 0.1 | > 0.25 | unexpected layout shift |

A page passes when all three are good for at least 75% of visits. Lab tools
(Lighthouse) and field data (CrUX/PSI/Search Console) answer different
questions. A green lab score does not prove field pass; a field fail is the
one users experience.

## LCP

Common causes and fixes:

- hero image lazy-loaded → remove `loading="lazy"`; use `fetchpriority="high"`
- hero discovered late (CSS background, JS slider) → render it as an `<img>`
  in the HTML
- render-blocking CSS/fonts → inline critical CSS, preload the font, avoid
  request chains
- slow TTFB → cache, database, hosting, redirects
- large image → responsive `srcset`/`sizes`, AVIF/WebP, correct dimensions
- client-side rendering → server-render the LCP content

## INP

INP is about the main thread being busy when the user interacts. Common causes:

- large JS bundles and hydration work
- third-party tags, chat widgets, A/B tools
- long tasks in event handlers
- too much work on first input

Fixes are engineering work: split code, defer non-critical scripts, yield to the
main thread, reduce hydration, remove unused dependencies. A code review can
find suspicious patterns, but field INP needs measurement.

## CLS

- Set `width`/`height` or `aspect-ratio` on images and video.
- Reserve space for ads, embeds, cookie banners and dynamic content.
- Avoid inserting content above existing content.
- Use `font-display` and preload to reduce font swap shift.
- Do not animate layout properties; use transform/opacity.

## Rendering and performance interaction

SSR/SSG improves LCP because the main content is in the first HTML response.
But SSR can also hurt if:

- the server waits on slow APIs before sending HTML (TTFB)
- the page streams critical content late
- hydration is heavy and blocks INP
- caching is misconfigured and every request hits the origin

A hybrid strategy is normal: static/SSR for public content, client rendering
for app screens, islands for interactive widgets.

## Code-level checks

- hero/LCP image: not lazy, has dimensions, modern format, `fetchpriority`
- render-blocking stylesheet count and `@import` chains
- blocking scripts without `defer`/`async`/`type=module`
- third-party fonts and scripts on the critical path
- images without dimensions
- large HTML payloads and excessive DOM (inspect, not a hard rule)
- cache headers for HTML and assets
- compression (Brotli/Gzip) at the server/CDN
- redirects before the final response
- SSR data fetching that serializes slow calls before HTML

## Measurement

- Field: CrUX, PageSpeed Insights, Search Console Core Web Vitals report.
- Lab: Lighthouse, WebPageTest; useful for debugging, not for proving field
  pass.
- RUM: add `web-vitals` or an equivalent to collect real-user LCP/INP/CLS.
- Compare templates, not individual URLs only; one template fix can move many
  pages.
- Measure before/after with the same device class, network and page sample.
