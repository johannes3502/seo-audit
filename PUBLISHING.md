# Publishing

Maintainer checklist for a public release.

## Preflight

- [ ] `python scripts/validate_skill.py .` prints `OK`.
- [ ] `python -m py_compile scripts/*.py` passes.
- [ ] `python -m unittest discover -s tests -v` passes.
- [ ] `SKILL.md` `name` is `seo-audit` and the repository root contains
      `SKILL.md`.
- [ ] `SKILL.md` version, `CHANGELOG.md` and the intended tag agree.
- [ ] No customer names, domains, keywords, secrets or generated reports are
      present (`rg -i "customer|internal-domain|api[_-]?key"`).
- [ ] `LICENSE` copyright holder is correct.
- [ ] README clone URLs and badges point at `johannes3502/seo-audit`.

## Create the public repository

With the GitHub CLI:

```bash
gh auth login
gh repo create seo-audit --public --source . --remote origin --push
```

Without `gh`, create the repository in the web UI, then:

```bash
git remote add origin https://github.com/johannes3502/seo-audit.git
git branch -M main
git push -u origin main
```

## Repository settings

Description:

> Evidence-based technical SEO audit skill for coding agents: codebase scan,
> live crawl, prioritized fix plan, optional GSC.

Topics:

`seo`, `seo-audit`, `technical-seo`, `agent-skills`, `ai-agents`, `kilo`,
`claude-code`, `codex`, `core-web-vitals`, `structured-data`, `python`

Security and collaboration:

- Enable Issues and Discussions (optional).
- Enable private vulnerability reporting.
- Enable secret scanning and push protection.
- Enable Dependabot alerts and security updates.
- Protect `main`: require CI, disallow force pushes, require a pull request.
- Protect tags matching `v*`.

## First release

```bash
git tag -a v0.4.0 -m "v0.4.0"
git push origin v0.4.0
gh release create v0.4.0 --title "v0.4.0" --notes-file CHANGELOG.md
```

## Kilo Marketplace

The marketplace indexes externally hosted skills; it does not host the code.

1. In a checkout of `Kilo-Org/kilo-marketplace`:
   `npx tsx bin/add-remote-skill.ts https://github.com/johannes3502/seo-audit/tree/main`
2. The script adds `metadata.source` (repository, path, license, commit).
3. Validate with `skills-ref validate .` and the marketplace checks, then open a
   PR.
4. Updates sync from this repository; no new PR per change is required.

Suggested category: `search`. Suggested filename triggers: `sitemap.xml`,
`robots.txt`, `next.config.js`, `nuxt.config.ts`, `svelte.config.js`,
`astro.config.mjs`.

## After publishing

- Verify the raw install: clone into an empty skills directory named
  `seo-audit` and ask an agent to review a small repository.
- Check the CI badge and the release page.
- Add the repository to relevant skill directories or awesome lists.
