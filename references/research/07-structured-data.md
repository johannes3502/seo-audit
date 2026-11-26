# Structured data

Sources: Google structured data intro, general guidelines, Organization,
LocalBusiness, Article, Search Gallery; Schema.org (see `00-sources.md`).

## What it is for

Structured data describes the page in a machine-readable vocabulary
(Schema.org). Google uses it for rich results and to understand entities. It is
not required for ranking and it does not guarantee a rich result.

## Format

- JSON-LD is Google's recommended format.
- Microdata and RDFa are supported, but harder to maintain.
- `data-vocabulary.org` is no longer eligible for Google rich results.

## General rules

- The markup must describe the visible page content. Do not mark up reviews,
  FAQs, prices or ratings that users cannot see.
- Include all properties required for the specific rich-result type. Missing
  required properties make the item ineligible.
- Fewer complete and accurate properties beat many incomplete/inaccurate ones.
- Put the markup on the page it describes. On duplicate pages, place the same
  markup on all duplicates, not only the canonical.
- Use the most specific applicable type.
- Image URLs in structured data must be crawlable and indexable.
- Do not block structured-data pages with robots.txt, noindex or login.
- Validate with the Rich Results Test and monitor the Search Console reports.

## Common types and minimum fields

These are practical checklist minima, not a substitute for the feature-specific
Google documentation.

### Organization

Recommended: `name`, `url`, `logo`, `sameAs`, `contactPoint`, `address`.
Place on the homepage or a single about page. No required properties in
Google's Organization guide, but a complete entity helps.

### LocalBusiness

Required: `name`, `address` (`PostalAddress`). Recommended: `telephone`, `url`,
`openingHours`, `geo`, `priceRange`, `sameAs`. Keep NAP consistent with the
visible page and Business Profile.

### Article / NewsArticle / BlogPosting

Recommended: `headline`, `image`, `datePublished`, `dateModified`, `author`,
`publisher`, `mainEntityOfPage`. The visible byline and date should match.

### Product

Required for merchant listings: `name`, `offers` (with `price`,
`priceCurrency`, `availability`). Add `image`, `brand`, `sku`, `review` or
`aggregateRating` only when real. Do not invent ratings.

### FAQPage

`mainEntity` is a list of `Question` items, each with `acceptedAnswer` and an
`Answer.text`. Only mark up FAQs that are visible on the page. Google has
limited FAQ rich-result display; markup is still useful for understanding, but
do not promise a rich result.

### BreadcrumbList

`itemListElement` with `ListItem` entries (`position`, `name`, `item`). Match
the visible breadcrumb.

## Common codebase failures

- JSON-LD is a template string with unescaped user data → invalid JSON or XSS.
- `@type` is correct but required fields are missing.
- Schema says `InStock` while the page says sold out.
- `aggregateRating` is hardcoded marketing copy, not real reviews.
- FAQ schema includes questions that are not visible.
- Organization name/address differs from the contact page.
- Multiple conflicting entities (two Organizations, two canonical URLs).
- Structured data exists only on desktop, not mobile (mobile-first indexing).
- Structured data is added client-side but never appears in the rendered HTML.

## Validation and iteration

1. Parse the JSON-LD as JSON in a test.
2. Check required fields for the chosen type.
3. Compare values with visible content.
4. Run the Rich Results Test on a deployed URL.
5. Check Search Console enhancements after deployment.
6. Keep the markup in sync with the page when prices, dates or availability
   change.
