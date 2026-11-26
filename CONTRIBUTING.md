# Contributing

Thanks for testing the skill. Keep changes small, evidence-based and generic.

## Add or change a rule

1. Pick a stable kebab-case ID; do not rename existing IDs.
2. Document severity, evidence fields and a concrete fix in
   `references/rules.md` (live) or `references/repo-rules.md` (codebase).
3. Implement the check in `seo_scan.py` or `repo_scan.py`.
4. Add a fixture or a reproducible URL where the rule fires.
5. Add a false-positive case: a page or repo that looks suspicious but is
   correct.
6. Update the research reference if the rule depends on a new source.
7. Update `README.md` if the public behavior changes.

## Add a framework adapter

1. Add detection in `repo_scan.py` before the static-HTML fallback.
2. Add a small fixture that mirrors the framework's real route and metadata
   conventions.
3. Add a negative case where the framework already handles the concern
   elsewhere (layout, plugin, server middleware).
4. Confirm the route count and the metadata source in the JSON output.

## No project profiles

Do not add customer- or project-specific rules, domains, keywords or route
names to the core skill. Put a sanitized example in `examples/` or build a
separate extension. The core must stay applicable to any repository.

## Style

- Python 3.10+, standard library only for the scanners.
- No secrets, tokens, customer data or private URLs in fixtures.
- Keep the scanner conservative: low concurrency, no bypassing bot protection,
  no crawling behind logins.
- No direct Google SERP scraping. Use a licensed API and say so.
- Keep user-facing scanner messages short and neutral. They may be German or
  English; the agent translates the report into the user's language.

## Pull requests

- One topic per PR.
- Include the command you ran and the relevant report excerpt.
- If a finding is intentionally downgraded, explain why and add a test.
- Run `python scripts/validate_skill.py .`, `python -m py_compile scripts/*.py`
  and `python -m unittest discover -s tests -v`.

## License

By contributing, you agree that your contribution is licensed under MIT.
