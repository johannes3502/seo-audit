# Google Search essentials

Sources: Google Search Essentials, Technical requirements, Spam policies,
Creating helpful content, SEO Starter Guide (see `00-sources.md`).

## Eligibility is not a ranking promise

A page must be crawlable, indexable and not spammy to be eligible. Google says
explicitly that meeting every requirement and best practice does not guarantee
crawling, indexing or serving. Never turn a green checklist into a traffic
forecast.

The minimum technical requirements are small:

- Googlebot is not blocked by `robots.txt` or a firewall/CDN rule.
- The page returns a crawlable status (normally `200`).
- The content is available in a supported format and is not behind a login.
- Important resources (CSS, JS, images) are crawlable if rendering needs them.
- The page is not `noindex` if it should appear in Search.

## What Google rewards

- Helpful, reliable, people-first content.
- Words people actually use, in prominent places: title, main heading, alt text,
  link text, and the visible body.
- Crawlable links so Google can discover other pages.
- Correct technical handling of images, video, structured data and JavaScript.

## Spam policies that matter to code reviews

- **Scaled content abuse**: generating many pages without added value.
- **Scraping**: republishing or lightly rewriting other people's content.
- **Keyword stuffing**: repeating words to manipulate ranking; also bad UX.
- **Doorway pages**: pages made to rank for a query and funnel users elsewhere.
- **Site reputation abuse**: third-party content on a site without real
  oversight.
- **Link spam**: paid or exchanged links; `rel="nofollow"`/`sponsored` for paid
  links.
- **Hidden text/links**: text or links hidden from users but shown to crawlers.

A codebase audit can detect some patterns (hidden text, keyword-stuffed titles,
auto-generated route families, cloaking branches by user agent). It cannot
prove intent. Report the evidence and let a human decide.

## E-E-A-T in one paragraph

E-E-A-T means experience, expertise, authoritativeness and trust. Google says it
is not a single ranking factor; its systems use a mix of signals. Trust is the
most important member, and YMYL topics (health, finance, safety, society) get
more weight. For a codebase, E-E-A-T is mostly about making the evidence
available: author pages, bylines, about/contact pages, sources, dates, clear
ownership, no fake reviews, no fabricated credentials.

## What a source scan can and cannot prove

Can prove from code:

- missing title/description/canonical/robots directives
- a CSR shell with no primary content in the initial HTML
- a catch-all route that returns `200` for unknown paths
- `noindex` in a shared layout
- a hardcoded canonical shared by every page
- missing or invalid hreflang
- missing alt/dimensions, non-crawlable anchors
- JSON-LD syntax and missing obvious fields
- sitemap/robots generators and their configuration

Cannot prove from code alone:

- whether Google indexed or ranked the page
- whether a title will be rewritten
- whether a page is "thin" in Google's eyes
- whether the content is helpful, accurate or trustworthy
- whether a backlink profile is strong
- whether Core Web Vitals pass in the field
- whether an AI feature cites the page

Live crawl evidence narrows the gap but still is not an index. Field data
(CrUX/PSI), Search Console and server logs are separate evidence sources.
