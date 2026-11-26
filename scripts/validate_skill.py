#!/usr/bin/env python3
"""Validate the seo-audit skill against the Agent Skills conventions.

Checks frontmatter, name/directory match, size budgets, referenced resources
and a few secret/path smells. No third-party dependencies.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MAX_SKILL_LINES = 500
MAX_DESCRIPTION = 1024
SECRET_PATTERNS = (
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
RESOURCE_PATTERN = re.compile(r"(?:scripts|references|assets|evals)/[A-Za-z0-9_./-]+")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("frontmatter is not closed with ---")
    raw = parts[1].strip().splitlines()
    data: dict[str, str] = {}
    for line in raw:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"').strip("'")
    return data, parts[2].lstrip("\n")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_skill.py <skill-dir>", file=sys.stderr)
        return 2
    skill_dir = Path(argv[1]).resolve()
    skill_file = skill_dir / "SKILL.md"
    errors: list[str] = []
    warnings: list[str] = []

    if not skill_file.exists():
        print(f"ERROR: missing {skill_file}", file=sys.stderr)
        return 1

    text = skill_file.read_text(encoding="utf-8")
    try:
        front, body = parse_frontmatter(text)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    name = front.get("name", "")
    description = front.get("description", "")
    license_name = front.get("license", "")

    if not name:
        errors.append("frontmatter.name is required")
    elif not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        errors.append("name must be lowercase kebab-case")
    elif name != skill_dir.name:
        errors.append(f"name '{name}' must match directory '{skill_dir.name}'")
    if not description:
        errors.append("frontmatter.description is required")
    elif len(description) > MAX_DESCRIPTION:
        errors.append(f"description is {len(description)} chars (max {MAX_DESCRIPTION})")
    if not license_name:
        errors.append("frontmatter.license is required")
    if len(body.splitlines()) > MAX_SKILL_LINES:
        errors.append(f"SKILL.md body is {len(body.splitlines())} lines (max {MAX_SKILL_LINES})")

    for match in RESOURCE_PATTERN.finditer(text):
        resource = match.group(0).rstrip(".,;:)`")
        if not (skill_dir / resource).exists():
            warnings.append(f"referenced resource does not exist: {resource}")

    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            errors.append(f"possible secret in SKILL.md: {pattern.pattern}")

    evals = skill_dir / "evals" / "evals.json"
    if evals.exists():
        try:
            data = json.loads(evals.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("evals"), list):
                errors.append("evals/evals.json must contain an 'evals' list")
        except json.JSONDecodeError as exc:
            errors.append(f"evals/evals.json is invalid JSON: {exc}")
    else:
        warnings.append("evals/evals.json is missing")

    for script in (skill_dir / "scripts").glob("*.py") if (skill_dir / "scripts").exists() else []:
        if script.name == "validate_skill.py":
            continue
        source = script.read_text(encoding="utf-8")
        if "C:\\Users\\" in source or "/home/" in source:
            warnings.append(f"possible machine-specific path in {script.name}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(source):
                errors.append(f"possible secret in {script.name}")

    print(f"Skill: {name or '(missing)'} · {skill_dir}")
    print(f"Description: {len(description)} chars · body: {len(body.splitlines())} lines")
    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
