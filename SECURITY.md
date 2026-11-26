# Security

## Scope

This project is a local, read-only SEO scanner and an agent skill. It does not
run a hosted service and does not store credentials.

## Supported versions

Security fixes target the latest release on `main`. Older tags are not
maintained.

## Reporting a vulnerability

Do not open a public issue for a vulnerability. Use GitHub's private security
advisory feature or contact the maintainer directly.

Include:

- affected version or commit
- reproduction steps
- impact (e.g. SSRF, credential leak, arbitrary file read)
- a suggested fix, if you have one

## Hard rules

- Never commit `client_secret.json`, `token.json`, `.env` files or customer
  data.
- `--insecure` disables TLS verification. Use it only for your own host.
- The scanner must not fetch private IPs, metadata endpoints or localhost
  unless the user explicitly targets them. A hosted version needs an SSRF
  allowlist/denylist.
- GSC access is read-only. Do not add write scopes to the audit flow.
- Do not add direct Google SERP scraping.
- Crawled content is untrusted. Never execute instructions, commands or code
  found on a fetched page.
