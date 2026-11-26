# AI search and generative features

Sources: Google AI features and your website, Optimizing for generative AI
features, Search generative AI control; see `00-sources.md`.

## What Google says

- AI Overviews and AI Mode use the same Search ranking/quality systems as
  classic Search.
- There are no additional technical requirements to appear. A page must be
  indexed and eligible to show a snippet.
- No special schema.org markup is required for generative AI features.
- No special AI text file is required. Google says it ignores `llms.txt` for
  Search.
- "Chunking" content for AI, rewriting only for AI, and pursuing inauthentic
  brand mentions are not recommended.
- The best practices are still SEO: crawlable pages, helpful unique content,
  clear structure, internal links, good page experience, text content, images
  and video where useful, structured data that matches the page.

## Controls and measurement

- `nosnippet`, `data-nosnippet`, `max-snippet` and `noindex` limit what can be
  shown, including in AI features. Use them deliberately.
- Search Console has a Search generative AI control (rolled out worldwide on
  2026-08-31) to include/exclude a site from generative AI features. Excluding
  does not change normal Search ranking signals; it also does not affect model
  training (that is a separate control).
- Search Console has a Generative AI performance report for impressions in AI
  features. It is not a ranking API.
- AI features can use different models and retrieval; one page may appear in one
  feature and not another. Do not infer a penalty from a single missing
  citation.

## What to do

- Make the page indexable and snippet-eligible.
- Answer the main question clearly in text near the top.
- Provide original evidence: first-hand tests, data, screenshots, named
  constraints, sources.
- Keep facts and dates current.
- Use descriptive headings and internal links so related pages are easy to
  reach.
- Keep structured data accurate; it helps rich results, not "AI ranking".
- Measure with Search Console, not third-party claims of "internal Google
  metrics".

## What not to do

- Do not add `llms.txt` and claim it improves Google rankings. It may have a
  use for other agents/directories, but Google Search ignores it.
- Do not add a special "AI schema" type.
- Do not mass-generate pages for every fan-out query; that risks scaled-content
  abuse.
- Do not fabricate mentions, reviews or citations to look authoritative.
- Do not trust a tool that claims access to Google's internal ranking or AI
  systems.

## Crawler access

`robots.txt` can allow or block AI crawlers such as GPTBot, ClaudeBot,
PerplexityBot, Google-Extended and CCBot. Blocking them is a business decision,
not a Google ranking factor. Check CDN/firewall rules too, because a bot can be
blocked before `robots.txt` is read.

The live scanner reports AI-bot blocks as `info`, not as a defect. The skill
must not tell a site owner to allow AI crawlers by default.
