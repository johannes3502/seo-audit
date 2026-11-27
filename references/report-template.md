# Report template

Use the user's language. Keep the main report short enough to act on; put the
full evidence in the JSON files.

## Two reports, one decision

A full review has two evidence sets:

- `repo-report.md` / `repo-report.json` — source-code findings.
- `report.md` / `report.json` — live crawl findings, only when a real domain
  was tested.

The `fix-plan.md` combines them. Do not merge a code `hypothesis` and a live
`confirmed` finding into one row without saying which is which.

## Structure

```markdown
# SEO Review — {repo or domain}

**Verdict:** {one sentence: is public content server-rendered, indexable and
aligned with its target intent?}

**Scope:** {repo root} · {framework/rendering} · {live pages if tested} ·
{date} · {limitations}

**Mode:** Review (no edits yet) or Apply (batches approved).

**Business context:** {local/regional/national/e-commerce/SaaS} | {countries/languages} |
{GBP? legal entity?} | {static HTML, page cap, date}

## 0b. Coverage ledger

| Area | Checked? | Evidence | Reference |
|---|---|---|---|
| Rendering | yes/no/partial | raw HTML, framework config | `ssr.md` |
| Indexing | ... | status, canonical, robots, sitemap | `codebase.md` / `live.md` |
| On-page | ... | title/H1/description | `codebase.md` |
| Content/E-E-A-T | ... | content sample | `codebase.md` |
| Local/entity | ... | NAP, schema, GBP (manual) | `local.md` |
| Trust/legal | ... | imprint, privacy, contact | `trust.md` |
| Performance | ... | lab/field, TTFB | `live.md` |
| Structured data | ... | JSON-LD, event eligibility | `local.md` |
| i18n | ... | locale URLs, hreflang | `live.md` |
| Events | ... | leaf URL, organizer, dates | `local.md` |

An unchecked area is not a clean area. State why it was not checked.

## 0. Scope and app inventory (umbrella/monorepo)

| Surface | Path | Type | Public? | Domain | Evidence | Score? |
|---|---|---|---|---|---|---|
| ... | `frontend/site` | frontend | yes | example.com | route registry, sitemap | yes |
| ... | `business` | docs/context | no | — | marketing TODO | no |
| ... | `tools/preview` | local tool | no | 127.0.0.1 | README | no |
| ... | `server/services/api` | backend | via nginx | example.com | FastAPI app | no |

Rules:
- Scan and score each **public** app root separately; never score an umbrella
  root, a docs repo, a local tool, an internal `noindex` app or a bare backend.
- A mixed host (internal app plus a public SSR route) is listed as `mixed` and
  gets a policy check, not a marketing score.
- `business/` is a context source for keywords/intent/TODOs, not a web route.
- State what was excluded and why (worktrees, third-party, screenshots,
  build output).

## 1. What the code says

| Area | Finding | Evidence | Confidence |
|---|---|---|---|
| Rendering | ... | file:line / raw HTML | confirmed/likely |
| Metadata | ... | file:line | ... |
| Indexing | ... | file:line | ... |
| Keywords | ... | route + keyword map | ... |
| Local/entity | ... | NAP, schema, GBP (manual) | ... |
| Trust/legal | ... | imprint, privacy, contact | ... |
| Events | ... | leaf URL, organizer, dates | ... |

## 2. What the live site says (if tested)

- raw HTML vs rendered HTML for key routes
- status/canonical/robots/sitemap
- soft-404 result
- headers/CDN/redirects
- differences from the code expectation

## 2b. Local, trust and events (if applicable)

- NAP on page/footer/imprint/schema/GBP; list the exact values checked.
- LocalBusiness type and fields; GBP/citations marked manual/not checked.
- Location and service-area pages: unique content, links, canonicals.
- Legal links: same host/entity; cross-domain links verified.
- Events: one leaf URL per event; list-page markup is not eligible; expired
  events removed or marked cancelled/postponed.

## 3. Top fixes

| # | Fix | Why it matters | Evidence | Effort | Risk | Owner |
|---:|---|---|---|---|---|---|
| 1 | ... | ... | URL/file + rule ID | S/M/L | low/med/high | dev/content/ops |

Rules:
- One row = one actionable change.
- Group template issues: "Article template: 412 pages share the same title".
- The "Why" is a mechanism, not a promise.
- Link to the evidence in JSON or a page section.
- Mark heuristics as `likely` and open questions as `hypothesis`.

## 4. What is already good

Three to five bullets. This prevents a generic audit and shows the scan was
read.

## 5. Fix batches for the review gate

| Batch | Scope | Files/routes | Effort | Risk | Depends on |
|---|---|---|---|---|---|
| A | Rendering/SSR | ... | ... | ... | — |
| B | Indexing/canonical/404 | ... | ... | ... | A |
| C | Titles/H1/descriptions | ... | ... | ... | — |
| D | Keywords/content/internal links | ... | ... | ... | C |
| E | Performance/CWV | ... | ... | ... | — |
| F | Structured data/i18n | ... | ... | ... | — |

Ask which batches to implement. Do not edit before the answer.

## 6. Route/template clusters

| Cluster | Routes | Main issue | Fix once | Affected routes |
|---|---:|---|---|---|
| Home | 1 | ... | ... | ... |
| Product | 240 | ... | ... | sample |

## 7. Keywords

- keyword map status (provided/created)
- owner URL per intent
- missing/weak title/H1/description coverage
- cannibalization candidates
- content gaps (manual, not invented)

## 8. Performance

Separate lab data (Lighthouse/PSI) from field data (CrUX). Never mix them.
State the device and date. A green lab score is not a field pass.

## 9. Search Console quick wins (if available)

- position 4–15 with impressions
- CTR gaps
- cannibalization candidates
- index coverage sample
- date range and row limit

Label every GSC number with its date range. Do not extrapolate traffic.

## 10. AI search (optional, corrected)

- normal SEO is the requirement; no special schema/file
- `llms.txt` is ignored by Google Search; do not present it as a Google fix
- AI-bot rules are a business decision
- Search Console generative AI report/control, if available

## 11. 30/60/90 plan

| Window | Focus | Done when |
|---|---|---|
| 0–30 days | rendering, crawl/indexing/canonical | critical/high closed |
| 30–60 days | templates, titles, internal links | top clusters fixed |
| 60–90 days | performance, schema, content | measured against baseline |

## 12. Method and limits

- repo files scanned, framework heuristics, route count
- live pages crawled, depth, user agent, date
- static HTML vs. JS rendering
- robots respected, rate limit
- no backlink index, no rank tracking, no Google scraping
- GSC: read-only, date range, row limit
- what could change the conclusion (JS, personalization, bot protection)

## 13. What was not checked

- GBP, citations, reviews and rankings (manual)
- JS-rendered DOM for routes not spot-checked
- GSC data outside the stated range
- any check marked `no` or `partial` in the coverage ledger
```

## Tone

- Direct, technical, no hype.
- "The canonical points to a different host" beats "SEO is bad".
- Separate observation, interpretation and recommendation:

```markdown
Observation: 412 article pages share the same title.
Interpretation: Google may rewrite the title or choose a different page for
the query; the template is the likely cause.
Recommendation: use the article H1 as the title source and append the brand.
```

- No fake urgency, no guaranteed rankings.
- If the data is insufficient, say so in the first paragraph.

## Evidence links

For each top fix, include at least one of:

- `file:line` and a short code snippet
- URL + HTTP status + raw HTML snippet
- GSC query + date range
- PSI/CrUX value + device

If you cannot produce evidence, downgrade the item to `hypothesis` and put it
in a separate "Open questions" section.

## Client-ready PDF

- Cover: domain/repo, date, scope, one-line verdict.
- Page 2: top fixes with effort/impact.
- Page 3–4: evidence and screenshots.
- Page 5: 30/60/90 plan and next step.
- Appendix: full issue list or link to JSON.

White-label only in the hosted product. The open-source report keeps the tool
name.
