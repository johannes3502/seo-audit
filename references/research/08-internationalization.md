# Internationalization and hreflang

Sources: Google localized versions, multi-regional/multilingual sites, x-default
blog post; see `00-sources.md`.

## URL strategy

Use different URLs for each language version. Avoid cookie/browser-language
redirects that hide versions from crawlers. Googlebot usually crawls from the
US and does not send `Accept-Language`, so a language redirect can prevent it
from seeing all variants.

Common patterns:

- `example.com/de/`, `example.com/en/`
- `de.example.com`, `en.example.com`
- `example.de`, `example.com`

Pick one and keep it stable. Use UTF-8 URLs and escape them correctly.

## hreflang rules

- Every page in a cluster lists itself and all other versions.
- Return links must be reciprocal; if page A links to B with hreflang, B must
  link back to A. Missing return links can cause the annotations to be ignored.
- Use ISO 639-1 language codes, optionally plus ISO 3166-1 Alpha 2 region:
  `de`, `de-DE`, `en-GB`, `zh-Hant`, `zh-Hans`.
- A region code alone is invalid; `en-UK` is not valid (`en-GB` is).
- `es-419`, `EU`, `UN` are not supported values.
- Add `x-default` for the fallback page (language selector, global homepage or
  the default version). It is recommended, not mandatory.
- Do not point all hreflang variants at one language's canonical. Each language
  version should be self-canonical.
- Use one implementation method consistently: HTML `<link>`, HTTP `Link`
  header, or XML sitemap. Combining methods is allowed but adds maintenance.

## Page language

- Set `<html lang="...">` for accessibility and parsing.
- Google says it primarily uses visible content to determine language, not the
  `lang` attribute. Keep each page in one language; avoid side-by-side
  translations in the body.
- Translate the visible UI, not only the boilerplate, if the body remains in
  another language.

## Codebase checks

- i18n framework/config present (`next-intl`, `@nuxtjs/i18n`, `svelte-i18n`,
  `react-i18next`, `vue-i18n`, Rails i18n, Django i18n).
- hreflang cluster generated per route, with self-reference and return links.
- canonical is self-referential per language.
- sitemap includes all localized URLs and hreflang annotations if used.
- `lang` attribute matches the page.
- no automatic redirect that makes non-default languages uncrawlable.
- locale switcher uses crawlable links, not only a client-side state change.

## Testing

1. Fetch a page with a non-default `Accept-Language`; the server should still
   return a crawlable page (no surprise redirect).
2. Inspect the `<head>` for the complete hreflang cluster.
3. Verify return links between a sample of variants.
4. Check canonical and hreflang agree.
5. Validate with a hreflang checker or a small script, then spot-check in Search
   Console's international targeting report when available.
