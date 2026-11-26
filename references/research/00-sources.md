# Research sources

Checked on 2026-11-25. Prefer the primary source when a claim matters. Google
updates these pages; the dates below are the "last updated" values shown on the
page when checked, not the date this skill copied the text.

## Google Search Central

| Topic | Source | Last updated |
|---|---|---|
| Search Essentials | https://developers.google.com/search/docs/essentials | 2025-12-10 |
| Technical requirements | https://developers.google.com/search/docs/essentials/technical | 2025-12-10 |
| Spam policies | https://developers.google.com/search/docs/essentials/spam-policies | 2026-11-23 |
| Creating helpful, reliable, people-first content | https://developers.google.com/search/docs/fundamentals/creating-helpful-content | 2026-10-05 |
| SEO Starter Guide | https://developers.google.com/search/docs/fundamentals/seo-starter-guide | 2025-12-10 |
| Title links | https://developers.google.com/search/docs/appearance/title-link | 2025-12-10 |
| Meta descriptions / snippets | https://developers.google.com/search/docs/appearance/snippet | 2026-04-20 |
| JavaScript SEO basics | https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics | 2026-03-04 |
| Dynamic rendering (not recommended long-term) | https://developers.google.com/search/docs/crawling-indexing/javascript/dynamic-rendering | 2025-12-10 |
| Rendering for content-driven apps | https://developers.google.com/solutions/content-driven/hosting/rendering | 2024-07-10 |
| Canonicalization | https://developers.google.com/search/docs/crawling-indexing/canonicalization | 2026-08-20 |
| Consolidate duplicate URLs | https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls | 2026-07-10 |
| Block indexing with noindex | https://developers.google.com/search/docs/crawling-indexing/block-indexing | 2025-12-10 |
| robots.txt specification | https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt | 2026-08-31 |
| Build and submit a sitemap | https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap | 2026-07-08 |
| Image sitemaps | https://developers.google.com/search/docs/crawling-indexing/sitemaps/image-sitemaps | 2025-12-10 |
| Redirects and Google Search | https://developers.google.com/search/docs/crawling-indexing/301-redirects | 2026-11-16 |
| HTTP status codes for crawlers | https://developers.google.com/crawling/docs/troubleshooting/http-status-codes | 2026-02-04 |
| Troubleshoot crawling errors / soft 404 | https://developers.google.com/search/docs/crawling-indexing/troubleshoot-crawling-errors | 2026-11-16 |
| Mobile-first indexing | https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing | 2025-12-10 |
| Localized versions / hreflang | https://developers.google.com/search/docs/specialty/international/localized-versions | 2026-09-21 |
| Multi-regional and multilingual sites | https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites | 2025-12-10 |
| Link best practices | https://developers.google.com/search/docs/crawling-indexing/links-crawlable | 2025-12-10 |
| Image SEO best practices | https://developers.google.com/search/docs/appearance/google-images | 2026-03-02 |
| Core Web Vitals and Search | https://developers.google.com/search/docs/appearance/core-web-vitals | 2025-12-10 |
| Structured data intro | https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data | 2025-12-10 |
| General structured data guidelines | https://developers.google.com/search/docs/appearance/structured-data/sd-policies | 2026-07-10 |
| Organization structured data | https://developers.google.com/search/docs/appearance/structured-data/organization | 2026-09-08 |
| LocalBusiness structured data | https://developers.google.com/search/docs/appearance/structured-data/local-business | current |
| Article structured data | https://developers.google.com/search/docs/appearance/structured-data/article | 2026-09-08 |
| AI features and your website | https://developers.google.com/search/docs/appearance/ai-features | 2025-12-10 |
| Optimizing for generative AI features | https://developers.google.com/search/docs/fundamentals/ai-optimization-guide | 2026-07-10 |
| Search generative AI control (Search Console) | https://support.google.com/webmasters/answer/16908024 | 2026-08-31 |

## web.dev / Core Web Vitals

| Topic | Source | Last updated |
|---|---|---|
| Web Vitals overview | https://web.dev/articles/vitals | 2024-10-31 |
| LCP | https://web.dev/articles/lcp | current |
| INP | https://web.dev/articles/inp | current |
| CLS | https://web.dev/articles/cls | current |
| Threshold methodology | https://web.dev/articles/defining-core-web-vitals-thresholds | 2025-05-07 |

## Framework documentation

| Framework | SEO surface | Source |
|---|---|---|
| Next.js App Router | Metadata API, sitemap, robots | https://nextjs.org/docs/app/getting-started/metadata-and-og-images · https://nextjs.org/docs/app/api-reference/file-conventions/metadata/sitemap · https://nextjs.org/docs/app/api-reference/file-conventions/metadata/robots |
| Nuxt | `useHead`, `useSeoMeta`, app head | https://nuxt.com/docs/getting-started/seo-meta · https://nuxt.com/docs/api/composables/use-seo-meta |
| Nuxt SEO modules | robots, sitemap | https://nuxtseo.com/docs/robots/getting-started/introduction · https://nuxtseo.com/docs/sitemap/getting-started/introduction |
| SvelteKit | SSR, `svelte:head`, page options, sitemap | https://svelte.dev/docs/kit/seo · https://svelte.dev/docs/kit/page-options · https://svelte.dev/docs/svelte/svelte-head |
| Astro | static output, sitemap integration, client directives | https://docs.astro.build/en/guides/integrations-guide/sitemap/ · https://docs.astro.build/en/reference/directives-reference/ · https://docs.astro.build/en/reference/configuration-reference/ |
| Remix / React Router | `meta` export, route modules | https://remix.run/docs/en/main/route/meta · https://reactrouter.com/start/framework/route-module · https://reactrouter.com/how-to/meta |

## Structured data vocabulary

| Topic | Source |
|---|---|
| Schema.org | https://schema.org/ |
| Rich Results Test | https://search.google.com/test/rich-results |
| Search Gallery (feature-specific rules) | https://developers.google.com/search/docs/appearance/structured-data/search-gallery |

## Notes on source quality

- Google documentation is the authority for Google Search behavior. Third-party
  SEO blogs are useful for workflow ideas, not for claims about Google's index.
- The Search Quality Rater Guidelines are a rater manual, not a ranking-factor
  list: https://guidelines.raterhub.com/searchqualityevaluatorguidelines.pdf
- Framework docs describe the intended API. The rendered HTML still has to be
  verified, because a framework default can be overridden per route.
