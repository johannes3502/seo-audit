# Content quality, E-E-A-T and trust

Sources: Google Creating helpful, reliable, people-first content; Search
Quality Rater Guidelines; AI-generated content guidance (see `00-sources.md`).

## What Google actually says

- Ranking systems aim to prioritize helpful, reliable information created for
  people, not to manipulate rankings.
- E-E-A-T (experience, expertise, authoritativeness, trust) is not a single
  ranking factor. Trust is the most important member; the others support it.
- YMYL topics (health, financial stability, safety, welfare of society) get more
  weight on E-E-A-T.
- AI-generated content is not automatically spam. The focus is quality and
  helpfulness, not how it was produced. Mass-producing pages without value is
  spam (scaled content abuse), regardless of whether a human or AI wrote them.
- Fabricated author profiles, AI headshots, fake credentials or fake reviews are
  deception and a trust problem.

## Questions to ask about a page

- Does it help the reader accomplish something, or only attract clicks?
- Does it demonstrate first-hand experience where that matters?
- Is the author identifiable, with relevant background?
- Are claims sourced, dated and verifiable?
- Is the site's ownership/contact information clear?
- Does the page exist in a coherent topic cluster, or is it an orphan?
- Is the content original, or a rewrite of the current SERP?
- Is it maintained, or visibly outdated?

There is no word-count or "E-E-A-T score" that answers these questions.

## Code-level trust signals a repo can provide

- author entity (`Person`) linked to an author page and `sameAs` profiles
- `Organization`/`LocalBusiness` data consistent with the visible contact page
- `datePublished` / `dateModified` in Article schema and visible byline/date
- about, contact, imprint, privacy pages linked from the footer
- review data backed by real reviews; do not invent `aggregateRating`
- sources/citations as real links, not plain text
- no hidden text, cloaking or fake freshness
- canonical and hreflang consistent with the content's language

## What not to automate

- Do not generate author bios, credentials or reviews.
- Do not invent statistics, citations, awards or customer logos.
- Do not add FAQ schema for questions that are not visible on the page.
- Do not create location pages with only the city name changed.

The skill can detect missing structural signals. It cannot judge whether the
content deserves trust; that needs a human with domain knowledge.
