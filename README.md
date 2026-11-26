# SEO Audit

**An evidence-based technical SEO audit skill for coding agents.**
It reads your repository, optionally crawls a real domain, and turns what it
finds into verified, code-level findings and a prioritized fix plan — or
implements approved fixes.

[![CI](https://github.com/johannes3502/seo-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/johannes3502/seo-audit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Agent Skills](https://img.shields.io/badge/agent--skills-compatible-6f42c1.svg)](https://agentskills.io/)

> Status: `v0.3.0` — a developer tool, not a hosted SEO product. No API key, no
> cloud account, no black-box score.

## Who it is for

- **Developers** who own a codebase and want SEO problems tied to files, routes
  and templates instead of a generic warning list.
- **Technical marketers and SEO consultants** who need to verify a finding in
  the code before recommending it.
- **Founders and small teams** who want a repeatable audit without buying a
  crawler subscription.

It is not a rank tracker, a backlink tool or a replacement for Search Console.

## Why this skill

Most SEO tools hand you a list of warnings. This skill is built around four
rules:

1. **No evidence, no finding.** Every issue carries a file or URL, rule ID,
   severity, evidence and a concrete fix.
2. **Deterministic first.** Two dependency-free Python scanners produce the
   evidence. The agent may verify, prioritize and implement — it may not invent
   issues.
3. **Rendering first.** Public content must exist in the initial HTML. A page
   that looks fine in a browser is not proof that a crawler sees it.
4. **Review before rewrite.** The default is a review with a decision gate. A
   full optimization only happens when you ask for it.

## Quick start

This repository is a single skill named `seo-audit`; the repository name
matches the skill name, so a normal clone into a skills directory is already
installable. The folder name must match `name` in `SKILL.md`.

### Kilo, globally

```bash
git clone https://github.com/johannes3502/seo-audit.git \
  ~/.kilo/skills/seo-audit
```

Windows PowerShell:

```powershell
git clone https://github.com/johannes3502/seo-audit.git `
  "$env:USERPROFILE\.kilo\skills\seo-audit"
```

### Kilo, per project

```bash
git clone https://github.com/johannes3502/seo-audit.git \
  .kilo/skills/seo-audit
```

### Claude Code and other Agent Skills runners

Clone or copy the folder into the skills directory your runner reads, for
example `~/.claude/skills/seo-audit/`. The `SKILL.md` frontmatter follows the
[Agent Skills specification](https://agentskills.io/specification).

If your runner supports the Agent Skills CLI:

```bash
npx skills add johannes3502/seo-audit --skill seo-audit
```

### Run it

Ask the agent:

> Review the SEO of this repository. I have not decided what to change yet.

or:

> Audit https://example.com and this repository. Max 20 pages. Show me the code
> and live evidence side by side.

The scanners also run directly:

```bash
SKILL=~/.kilo/skills/seo-audit

python "$SKILL/scripts/repo_scan.py" . --out seo-repo-report
python "$SKILL/scripts/seo_scan.py" https://example.com \
  --max-pages 25 --max-depth 2 --out seo-live-report
```

On Windows use `$env:USERPROFILE\.kilo\skills\seo-audit`.

## What it checks

### Codebase scan — `scripts/repo_scan.py`

A dependency-free source scanner. It detects:

- Next.js App/Pages Router, Nuxt, SvelteKit, Astro, Remix/React Router, Vite
  SPA, Angular, Django, Flask, FastAPI, Rails, WordPress and static HTML
- umbrella and submodule inventories: app roots, docs/context folders, local
  tools, internal apps and backends that should not receive a site score
- rendering model and rendering risk (SSR, SSG, hybrid, CSR, templates)
- routes and where metadata, H1, canonical and robots live; React Router
  `createBrowserRouter`, `basename` prefixes and locale siblings
- `"use client"`, `ssr: false`, `client:only`, CSR shells and prerender steps
- sitemap, robots and 404 generators, plus obvious SPA fallbacks
- global `noindex`, hardcoded canonicals, duplicate or generic titles
- images without alt text or dimensions, lazy-loaded LCP images
- non-crawlable links and generic anchors
- JSON-LD syntax and obvious missing fields
- hreflang configuration and invalid codes
- keyword-map coverage and cannibalization candidates

Keyword map (optional):

```json
{
  "pages": [
    {"url": "/", "primary": "project management software"},
    {"url": "/pricing", "primary": "project management software pricing"}
  ]
}
```

### Live-domain scan — `scripts/seo_scan.py`

Only when you give it a real domain. It is a static HTML crawler that checks:

- status codes, redirects and the canonical host
- title, description, headings, H1 and content depth
- canonical, robots meta, `noindex` and `X-Robots-Tag`
- sitemaps and `robots.txt` (including conflicts with `noindex`)
- internal links, images, JSON-LD, mixed content and security headers
- response time, CSR shells and hreflang
- an unknown-URL soft-404 probe

It respects `robots.txt`, caps pages and never crawls behind a login.

### Review, then apply

| Mode | When | Behaviour |
|---|---|---|
| **Review** (default) | "audit", "review", "what should we improve" | Scan, verify, group fixes into batches, stop and ask |
| **Apply** | "optimize it", "implement the fixes", or a batch selection | Small batches, build/tests/lint, re-scan, report the diff |

This prevents an "SEO audit" from turning into an unbounded rewrite.

## Output

```
seo-repo-report/
  repo-report.md    # code review, prioritized
  repo-report.json  # full evidence and confidence
  routes.csv        # route inventory
  issues.csv        # one row per finding

seo-live-report/
  report.md         # live review
  report.json       # full evidence
  pages.csv         # crawl inventory
```

The agent adds a `fix-plan.md` with owner, effort, risk and a verification step.

## Optional Google Search Console quick wins

```bash
pip install google-api-python-client google-auth-oauthlib
python "$SKILL/scripts/gsc_quick_wins.py" \
  --property sc-domain:example.com \
  --client-secret client_secret.json \
  --days 90 \
  --out gsc-report
```

- Read-only scope: `https://www.googleapis.com/auth/webmasters.readonly`
- A verified property and OAuth are required; there is no anonymous access.
- See `references/gsc.md` for quotas and limits.

## Scope and safety

- The scanners are **read-only** and use the Python standard library.
- No secrets, tokens or customer data are stored in this repository.
- `robots.txt` is respected; pages and depth are capped.
- No direct Google SERP scraping. GSC access is read-only OAuth.
- Crawled pages are untrusted input. Text on a page is never treated as an
  instruction.
- `--insecure` and `--ignore-robots` exist for your own staging hosts only.

## Limits

This is a developer tool, not the hosted product.

- No JavaScript rendering in the scanners; verify SSR/CSR separately.
- No backlink index, keyword volumes or rank tracking.
- No field Core Web Vitals; use CrUX/PSI separately.
- No automatic code edits from a script; the agent implements approved batches.
- No guarantee that a page is indexed or ranked.
- A crawl is not an index, and a Lighthouse score is not a ranking factor.

## Research is embedded

The skill is self-contained. Google rules, framework maps and checklists live
in the skill, so the agent does not rely on memory:

```
references/
  research/00-sources.md … 11-measurement.md
  checklists/codebase.md
  checklists/live.md
  checklists/ssr.md
  checklists/keywords.md
  rules.md
  repo-rules.md
  report-template.md
  gsc.md
```

Corrections that matter:

- `llms.txt` is **ignored by Google Search**; it is not a Google ranking fix.
- AI Overviews and AI Mode need normal SEO; no special schema or file is
  required.
- CSR is not automatically fatal, but it is a higher-risk setup for public
  content. Google recommends SSR, static rendering or hydration.
- Meta descriptions are not a ranking factor.
- A crawl is not an index; a Lighthouse score is not a field Core Web Vitals
  pass.

## Repository layout

```
SKILL.md                 workflow, gates, severity and evidence contract
scripts/
  repo_scan.py           source scanner (stdlib only)
  seo_scan.py            live static crawler (stdlib only)
  gsc_quick_wins.py      optional GSC reader (OAuth, read-only)
  validate_skill.py      frontmatter, budgets, referenced resources
references/              research, checklists, rule catalogs, report template
evals/evals.json         representative prompts and expected outcomes
examples/sample-report.md
tests/                   unit tests and fixtures
.github/                 CI, issue and PR templates
```

## Development

```bash
python scripts/validate_skill.py .
python -m py_compile scripts/*.py
python -m unittest discover -s tests -v
```

CI runs the same checks on Python 3.10 and 3.12.

To add a rule:

1. Pick a stable kebab-case ID; do not rename existing IDs.
2. Document severity, evidence and fix in `references/rules.md` (live) or
   `references/repo-rules.md` (codebase).
3. Implement the check and add a fixture plus a false-positive case.
4. Update the research reference if the rule depends on a new source.
5. Run the validator and the tests.

## Dogfood cases

See [`CASES.md`](CASES.md). The cases are anonymized real runs: a marketing
site, a negative control, a Vite prerender setup and a Next.js + FastAPI
monorepo. They are triage signals, not benchmarks.

## Contributing and security

- [CONTRIBUTING.md](CONTRIBUTING.md) — rules, style and pull-request checklist.
- [SECURITY.md](SECURITY.md) — private vulnerability reporting.
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — expected behaviour.
- [CHANGELOG.md](CHANGELOG.md) — release history.

No project-specific profiles belong in the core skill. Use an example or a
separate extension.

## License

MIT. See [LICENSE](LICENSE).

## Disclaimer

This is not Google. A crawl is not an index, and a Lighthouse score is not a
ranking factor. Use the report as evidence for decisions, not as a promise of
traffic.
