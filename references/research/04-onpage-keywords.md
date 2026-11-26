# On-page SEO and keyword optimization

Sources: Google SEO Starter Guide, title links, snippets, links best practices,
helpful content; industry material on intent and topical authority is marked as
practice, not Google rules.

## The keyword map is the missing input

A codebase cannot know the business goal. Before optimizing, establish:

- one **owner URL** per search intent
- a **primary keyword** per owner URL
- optional secondary phrases and synonyms
- the target country/language
- the money pages and conversion goal

Store it as JSON so the scanner can check coverage:

```json
{
  "pages": [
    {"url": "/", "primary": "project management software", "secondary": ["team task tracker"]},
    {"url": "/pricing", "primary": "project management software pricing", "secondary": ["per-seat cost"]}
  ]
}
```

Without a keyword map, the review can still find structural problems, but it
must not pretend to know which query a page should own.

## Search intent

Classify each target before writing metadata:

| Intent | Typical query | Page job |
|---|---|---|
| Informational | how, what, why, guide | answer the question, then offer next step |
| Commercial investigation | best, vs, alternatives, review | compare options honestly |
| Transactional | buy, price, book, download | make the action obvious |
| Navigational | brand, login, contact | get the user to the right place |
| Local | service + city | prove location, service area, contact |

The page format should match the intent. A product page is a poor answer to a
"how does X work" query; a 3,000-word guide is a poor answer to "book a table".

## Title

- Unique per page, descriptive, concise; Google has no fixed character limit,
  but display is truncated by width (roughly 50-60 characters is a safe writing
  target).
- Put the distinguishing topic first, brand last if space allows.
- Avoid "Home", "Services", "Untitled", "React App", "Vite + React".
- Do not stuff variants. Google explicitly calls keyword stuffing spammy.
- The title should agree with the visible H1 and page content; Google may
  rewrite a title that is inaccurate, outdated, half-empty or duplicated.
- A template like `%s | Brand` is fine; a template that produces the same title
  for every page is not.

## Meta description

- Not a ranking factor. Google may use it for the snippet when it describes the
  page better than on-page text.
- Unique, human-readable, one or two sentences, main point in the first
  120-160 characters.
- Include the specific benefit, audience and next step; avoid keyword lists.
- Google can rewrite it per query; treat it as a suggestion, not a command.

## Headings

- One H1 that states the page topic in the user's words.
- H2 for main sections, H3 for subsections; do not skip levels for styling.
- Google says heading order is not a direct ranking factor, but structure helps
  users, screen readers and content understanding. A logical outline is still
  the right default.
- Do not use a logo/site name as an H1 on every page; that creates a second H1
  and weakens the page topic.
- A page with no H1 is a missed signal, not an automatic penalty. Flag it and
  check whether a layout renders one.

## Body and keyword use

- Cover the topic, not the phrase. Use the primary phrase naturally in the
  title, H1, opening paragraph and one or two subheadings.
- Use synonyms and related entities; do not repeat the exact phrase unnaturally.
- Answer the main question early, then add detail. This helps users and makes
  the page easier to quote/cite.
- Do not create pages for every keyword variant. Google's scaled-content-abuse
  policy targets mass-produced pages with little value. One strong page per
  intent beats ten thin variants.
- Word count is not a ranking target. Thin content is a content-quality
  diagnosis, not "under 300 words = bad".

## URLs

- Short, readable, stable; use words, not IDs, when the words are meaningful.
- One canonical form: choose trailing slash or no trailing slash and keep
  internal links, canonical, sitemap and redirects consistent.
- Avoid changing URLs without a 301 map.
- Lowercase is the safe default; avoid spaces and unnecessary parameters.

## Images

- Use `<img>`/`<picture>` with a real `src`; Google does not index CSS
  background images as page images.
- Alt text describes the image's purpose in context; decorative images use
  `alt=""`.
- Do not stuff keywords into alt text.
- Use descriptive filenames as a light signal (`inventory-dashboard.webp`
  beats `IMG_4821.webp`).
- Provide `width`/`height` or an aspect ratio to avoid CLS.
- The hero/LCP image should not be lazy-loaded; use `fetchpriority="high"` when
  appropriate.

## Internal links

- Google can crawl a link when it is an `<a>` with a real `href`. A `<div
  onclick>` or a button that navigates by script is not a reliable crawlable
  link.
- Every page you care about should have at least one internal link from another
  page.
- Anchor text should be descriptive and make sense out of context. "Click here"
  and "read more" fail; "Inventory management for restaurants" works.
- Link to the canonical URL, not a redirect or duplicate.
- Do not mark normal internal links `nofollow`.
- There is no magic number of links per page; if a page feels like a link dump,
  it probably is.
- Topic clusters (hub + supporting pages) help users and crawlers understand
  relationships, but do not force a link between every page. Link where it is
  genuinely useful.

## Cannibalization

Two pages targeting the same intent compete with each other. Signs:

- the same primary keyword is mapped to multiple URLs
- two pages swap positions for the same query
- one page ranks for a definition while the money page gets nothing

Fix by choosing one owner, merging content, redirecting the weaker URL, or
re-targeting it to a distinct intent. Do not "optimize" both harder.

## What to check in code

- route-specific title/description/H1/canonical
- title templates that produce duplicates or generic titles
- keyword map coverage for priority routes
- heading outline and duplicate H1s
- image alt/dimensions/LCP loading
- anchor text and non-crawlable navigation
- internal links to redirects, 404s or noindex pages
- orphan routes not linked from navigation or content
- language/locale consistency
