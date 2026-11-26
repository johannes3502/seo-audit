#!/usr/bin/env python3
"""Evidence-based repository SEO scanner.

Reads a codebase, detects the rendering model and the places where SEO
metadata, routes, sitemaps, robots rules, canonicals, headings, images,
structured data and keyword targets live. It never edits files and never
crawls a live site.

The output is evidence for an agent, not a ranking prediction. Every finding
has a file, a line when available, a rule ID, a severity and a confidence
level. Heuristics are marked ``likely`` or ``hypothesis`` so the agent must
verify them in the code before changing anything.

Usage:
    python repo_scan.py . --out seo-repo-report
    python repo_scan.py . --keywords seo-keywords.json
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

VERSION = "0.2.4"
TOOL_NAME = "seo-audit-repo"

SEVERITY_WEIGHT = {"critical": 10, "high": 5, "medium": 2, "low": 1, "info": 0}
MAX_BYTES = 512 * 1024

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "bower_components", "vendor",
    "dist", "build", "out", "coverage", ".next", ".nuxt", ".output", ".svelte-kit",
    ".astro", ".cache", ".turbo", ".vercel", ".netlify", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "venv", ".venv", "env", ".env", "site-packages",
    "test-results", "playwright-report", ".idea", ".vscode", "target", "bin", "obj",
    ".prerender", "mockups",
}

TEXT_EXTENSIONS = {
    ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".vue", ".svelte", ".astro",
    ".html", ".htm", ".xhtml", ".py", ".php", ".rb", ".erb", ".jinja", ".jinja2",
    ".j2", ".twig", ".hbs", ".ejs", ".pug", ".cshtml", ".razor", ".gohtml", ".tmpl",
    ".md", ".mdx", ".json", ".xml", ".txt", ".yml", ".yaml", ".toml", ".ini",
    ".conf", ".config", ".css", ".scss", ".sass", ".less", ".graphql", ".gql",
}

SPECIAL_NAMES = {
    "dockerfile", "nginx.conf", "robots.txt", "sitemap.xml", "sitemap_index.xml",
    "package.json", "composer.json", "gemfile", "requirements.txt", "pyproject.toml",
    "next.config.js", "next.config.mjs", "next.config.ts", "nuxt.config.ts",
    "nuxt.config.js", "svelte.config.js", "astro.config.mjs", "astro.config.ts",
    "remix.config.js", "vite.config.js", "vite.config.ts", "vercel.json",
    "netlify.toml", "web.config", ".htaccess", "angular.json",
}

SPECIAL_SUFFIXES = (".config.js", ".config.mjs", ".config.ts", ".config.cjs")

FRAMEWORK_LABELS = {
    "next-app": "Next.js App Router",
    "next-pages": "Next.js Pages Router",
    "nuxt": "Nuxt",
    "sveltekit": "SvelteKit",
    "astro": "Astro",
    "remix": "Remix / React Router",
    "vite-spa": "Vite SPA",
    "angular": "Angular",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "rails": "Rails",
    "wordpress": "WordPress",
    "static": "Static HTML",
    "unknown": "Unknown",
}

RENDERING_LABELS = {
    "ssr": "Server-rendered (SSR)",
    "ssg": "Static generation (SSG)",
    "hybrid": "Hybrid / per-route rendering",
    "csr": "Client-side rendered (CSR)",
    "server-templates": "Server templates",
    "static": "Static files",
    "unknown": "Unknown",
}

GENERIC_TITLES = {
    "home", "start", "startseite", "untitled", "new page", "document",
    "react app", "vite + react", "vite + vue", "nuxt app", "sveltekit",
    "astro basics", "my app", "my website", "website", "app", "index",
}

GENERIC_ANCHORS = {
    "click here", "read more", "learn more", "more", "here", "this page",
    "hier", "mehr", "weiterlesen", "mehr erfahren", "klick hier", "dieser link",
}

AI_BOTS = ("GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended", "CCBot")

# Draft markers in real content. Bare "draft"/"Entwurf" is intentionally not
# enough: product names and CMS status labels use the same words.
DRAFT_MARKERS = re.compile(
    r"(\bseite\s+in\s+arbeit\b|\bin\s+arbeit\b|\bcoming\s+soon\b|"
    r"\bwork\s+in\s+progress\b|\bplatzhalter\b|\bunter\s+konstruktion\b|"
    r"\bseite\s+im\s+aufbau\b|\btodo\s*:|\bdraft\s+(?:version|page)\b|"
    r"\bunver[oö]ffentlicht\b)",
    re.I,
)

INTERNAL_SEGMENTS = {
    "admin", "dashboard", "backoffice", "internal", "intern", "console",
    "staff", "ops", "cms", "auth", "login", "account", "preview",
}



def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def line_of(text: str, match: re.Match[str] | int) -> int:
    index = match.start() if hasattr(match, "start") else int(match)
    return text.count("\n", 0, index) + 1


def snippet(text: str, match: re.Match[str] | int, width: int = 180) -> str:
    index = match.start() if hasattr(match, "start") else int(match)
    start = max(0, index - width // 3)
    end = min(len(text), index + width)
    return re.sub(r"\s+", " ", text[start:end]).strip()


def add_issue(
    issues: list[dict[str, Any]],
    rule: str,
    severity: str,
    category: str,
    message: str,
    file: Path | str = "",
    line: int = 0,
    evidence: dict[str, Any] | None = None,
    fix: str = "",
    confidence: str = "confirmed",
    docs: str = "",
) -> None:
    issues.append(
        {
            "rule": rule,
            "severity": severity,
            "category": category,
            "message": message,
            "file": str(file) if file else "",
            "line": line,
            "evidence": evidence or {},
            "fix": fix,
            "confidence": confidence,
            "docs": docs,
        }
    )


def iter_files(
    root: Path,
    max_files: int,
    excludes: list[str] | None = None,
    include_dist: bool = False,
) -> tuple[list[Path], int]:
    files: list[Path] = []
    skipped = 0
    patterns = [pattern.strip() for pattern in (excludes or []) if pattern.strip()]
    skip_dirs = set(SKIP_DIRS)
    if include_dist:
        skip_dirs -= {"dist", "build", "out", ".output"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            name for name in dirnames
            if name not in skip_dirs and not name.startswith(".git")
        )
        for name in sorted(filenames):
            path = Path(dirpath) / name
            rel = relpath(path, root)
            if any(fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(name, pattern) for pattern in patterns):
                skipped += 1
                continue
            suffix = path.suffix.lower()
            if suffix not in TEXT_EXTENSIONS and name.lower() not in SPECIAL_NAMES and not name.lower().endswith(SPECIAL_SUFFIXES):
                continue
            try:
                if path.stat().st_size > MAX_BYTES:
                    skipped += 1
                    continue
            except OSError:
                skipped += 1
                continue
            files.append(path)
            if len(files) >= max_files:
                return files, skipped
    return files, skipped


def read_text(path: Path) -> str:
    """Read text robustly (UTF-8/UTF-8-BOM/UTF-16/latin-1 fallback).

    Windows tools (PowerShell `>`, some editors) write UTF-16; a plain
    `read_text(encoding="utf-8")` silently turns that into mojibake or drops
    NUL-separated letters, which makes dependency/route detection fail.
    """
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return data.decode("utf-16")
        except UnicodeDecodeError:
            pass
    if data.count(b"\x00") > max(2, len(data) // 8):
        for encoding in ("utf-16-le", "utf-16-be", "utf-16"):
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="ignore")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(read_text(path) or "{}")
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}



def relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def load_packages(files: Iterable[Path], root: Path) -> tuple[dict[str, Any], list[str]]:
    merged: dict[str, Any] = {}
    package_files: list[str] = []
    for path in files:
        if path.name != "package.json":
            continue
        data = read_json(path)
        if not data:
            continue
        package_files.append(relpath(path, root))
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            merged.update(data.get(key) or {})
    return merged, package_files


def detect_framework(root: Path, files: list[Path], deps: dict[str, Any]) -> str:
    rels = {relpath(path, root) for path in files}
    names = {path.name for path in files}
    has = lambda *needles: any(needle in deps for needle in needles)  # noqa: E731

    if "next" in deps or any(name.startswith("next.config.") for name in names):
        app_routes = [
            rel for rel in rels
            if re.match(r"(?:.*/)?(?:src/)?app/(?:.*/)?(?:page|layout|route)\.(?:js|jsx|ts|tsx|mdx)$", rel, re.I)
        ]
        if app_routes:
            return "next-app"
        return "next-pages"
    if "nuxt" in deps or "nuxt.config.ts" in names or "nuxt.config.js" in names:
        return "nuxt"
    if "@sveltejs/kit" in deps or any(rel.startswith("src/routes/") for rel in rels):
        return "sveltekit"
    if "astro" in deps or "astro.config.mjs" in names or "astro.config.ts" in names:
        return "astro"
    if has("@remix-run/react", "@remix-run/node", "@react-router/dev") or any(rel.startswith("app/routes/") for rel in rels):
        return "remix"
    if "@angular/core" in deps or "angular.json" in names:
        return "angular"
    if "vite" in deps and has("react", "vue", "svelte", "solid-js"):
        return "vite-spa"
    if any(name.startswith("vite.config.") or name.startswith("vite.prerender.config.") for name in names):
        return "vite-spa"
    python_files = [
        rel for rel in rels
        if rel.lower().endswith(("requirements.txt", "pyproject.toml")) and rel.count("/") <= 2
    ]
    python_deps = " ".join(read_text(root / rel).lower() for rel in python_files)
    if not python_deps:
        # Service folders often rely on a parent requirements.txt or only declare
        # the framework in code. Read a bounded set of local Python entry points.
        py_sources = [
            read_text(path)[:4000].lower()
            for path in files
            if path.suffix.lower() == ".py" and relpath(path, root).count("/") <= 3
        ][:80]
        python_deps = " ".join(py_sources)
    if "django" in python_deps or any(rel.endswith("urls.py") for rel in rels):
        return "django"
    if "flask" in python_deps:
        return "flask"
    if "fastapi" in python_deps:
        return "fastapi"
    if "rails" in read_text(root / "Gemfile").lower() or any(rel.startswith("app/views/") for rel in rels):
        return "rails"
    if any(rel.endswith("wp-config.php") for rel in rels) or any(rel.startswith("wp-content/") for rel in rels):
        return "wordpress"
    root_html = any(rel.lower() in ("index.html", "index.htm", "public/index.html") for rel in rels)
    if root_html:
        return "static"
    return "unknown"


def detect_rendering(framework: str, files: list[Path], root: Path) -> tuple[str, str, list[str]]:
    rels = {relpath(path, root) for path in files}
    notes: list[str] = []
    if framework in ("next-app", "next-pages", "nuxt", "sveltekit", "remix"):
        return "ssr", "low", ["Framework renders HTML on the server or at build time by default."]
    if framework == "astro":
        return "ssg", "low", ["Astro renders static HTML by default; client:only islands can still hide content."]
    if framework in ("django", "flask", "fastapi", "rails", "wordpress"):
        return "server-templates", "low", ["HTML is produced by server templates."]
    if framework == "static":
        return "static", "low", ["Plain HTML files are served as-is."]
    if framework in ("vite-spa", "angular"):
        prerender = any("prerender" in path.name.lower() for path in files)
        if prerender:
            return "hybrid", "medium", [
                "A prerender configuration was found, but the source HTML shell is still client-rendered.",
                "Verify the built HTML, not only the source, before treating public routes as server-rendered.",
            ]
        return "csr", "high", ["The app ships a shell and renders public content in the browser."]
    return "unknown", "medium", ["Rendering model could not be determined."]


def route_from_next_app(rel: str) -> str:
    path = rel
    if "/app/" in path:
        path = path.split("/app/", 1)[1]
    elif path.startswith("app/"):
        path = path[len("app/"):]
    parts = path.split("/")
    if parts:
        parts = parts[:-1] if parts[-1].split(".")[0] in ("page", "route") else parts
    cleaned: list[str] = []
    for part in parts:
        if part.startswith("(") and part.endswith(")"):
            continue
        if part.startswith("[[...") and part.endswith("]]"):
            cleaned.append("*")
        elif part.startswith("[...") and part.endswith("]"):
            cleaned.append("*")
        elif part.startswith("[") and part.endswith("]"):
            cleaned.append(":" + part[1:-1])
        else:
            cleaned.append(part)
    route = "/" + "/".join(cleaned)
    return route.replace("//", "/").rstrip("/") or "/"


def route_from_pages(rel: str, prefix: str) -> str:
    path = rel
    if path.startswith(prefix):
        path = path[len(prefix):]
    path = re.sub(r"\.(js|jsx|ts|tsx|vue|astro|md|mdx)$", "", path, flags=re.I)
    if path.endswith("/index"):
        path = path[: -len("/index")]
    elif path == "index":
        path = ""
    parts = [part for part in path.split("/") if part and not (part.startswith("(") and part.endswith(")"))]
    cleaned = []
    for part in parts:
        if part.startswith("[...") and part.endswith("]"):
            cleaned.append("*")
        elif part.startswith("[") and part.endswith("]"):
            cleaned.append(":" + part[1:-1])
        else:
            cleaned.append(part)
    return "/" + "/".join(cleaned)


def route_from_remix(rel: str) -> str:
    path = rel
    if path.startswith("app/routes/"):
        path = path[len("app/routes/"):]
    path = re.sub(r"\.(js|jsx|ts|tsx)$", "", path, flags=re.I)
    if path.endswith("_index"):
        path = path[: -len("_index")]
    path = path.replace("$", ":").replace(".", "/").replace("_", "/")
    return "/" + path.strip("/")


def route_from_static(rel: str) -> str:
    path = re.sub(r"\.html?$", "", rel, flags=re.I)
    if path.endswith("/index") or path == "index":
        path = path[: -len("/index")] if path.endswith("/index") else ""
    return "/" + path.strip("/")


def build_route_map(files: Iterable[Path], root: Path) -> dict[str, list[str]]:
    """Map a page component name to every route from common client routers.

    Supports JSX ``<Route>`` trees, object route configs used by
    ``createBrowserRouter``/``useRoutes`` and a ``basename`` prefix. A component
    may legitimately be used by more than one route (for example ``/de/`` and
    ``/en/``); keep all siblings instead of de-duplicating to the first one.
    """
    route_map: dict[str, list[str]] = {}
    candidates = {
        "app.jsx", "app.tsx", "app.js", "app.ts", "router.jsx", "router.tsx",
        "router.js", "router.ts", "routes.jsx", "routes.tsx", "routes.js", "routes.ts",
    }
    ignore = {"Layout", "LoginLayout", "Suspense", "Navigate", "Route", "Routes", "Outlet", "Children"}

    def add(component: str, route: str, base: str) -> None:
        component = component.strip()
        route = (route or "").strip()
        if not component or component in ignore or not route or route == "*":
            return
        if route == "index":
            route = base or "/"
        if not route.startswith("/"):
            route = "/" + route
        if base and not route.startswith(base + "/") and route != base:
            route = base.rstrip("/") + route
        route_map.setdefault(component, [])
        if route not in route_map[component]:
            route_map[component].append(route)

    for path in files:
        if path.name.lower() not in candidates:
            continue
        text = read_text(path)
        basename_match = re.search(r"\bbasename\s*:\s*['\"]([^'\"]+)['\"]", text)
        base = basename_match.group(1).rstrip("/") if basename_match else ""

        for line in text.splitlines():
            if "<Route" not in line:
                continue
            path_match = re.search(r"\bpath\s*=\s*['\"]([^'\"]+)['\"]", line)
            if not path_match:
                continue
            components = re.findall(r"<([A-Z][A-Za-z0-9_]+)", line)
            components += re.findall(r"\bComponent\s*=\s*\{?\s*([A-Z][A-Za-z0-9_]+)", line)
            for component in components:
                add(component, path_match.group(1), base)

        for match in re.finditer(r"<Route\b([\s\S]*?)(?:/>|</Route>)", text):
            attrs = match.group(1)
            path_match = re.search(r"\bpath\s*=\s*['\"]([^'\"]+)['\"]", attrs)
            if not path_match:
                continue
            components = re.findall(r"<([A-Z][A-Za-z0-9_]+)", attrs)
            components += re.findall(r"\bComponent\s*=\s*\{?\s*([A-Z][A-Za-z0-9_]+)", attrs)
            for component in components:
                add(component, path_match.group(1), base)

        for match in re.finditer(
            r"\bpath\s*:\s*['\"]([^'\"]+)['\"][\s\S]{0,500}?"
            r"(?:element\s*:\s*\{?\s*<([A-Z][A-Za-z0-9_]+)|"
            r"Component\s*:\s*([A-Z][A-Za-z0-9_]+)|"
            r"component\s*:\s*([A-Z][A-Za-z0-9_]+)|"
            r"component\s*=\s*\{?\s*([A-Z][A-Za-z0-9_]+))",
            text,
        ):
            component = match.group(2) or match.group(3) or match.group(4) or match.group(5)
            add(component, match.group(1), base)

        for line in text.splitlines():
            path_match = re.search(r"\bpath\s*:\s*['\"]([^'\"]+)['\"]", line)
            if not path_match:
                continue
            components = re.findall(r"<([A-Z][A-Za-z0-9_]+)", line)
            components += re.findall(r"\b(?:Component|component)\s*=\s*\{?\s*([A-Z][A-Za-z0-9_]+)", line)
            for component in components:
                add(component, path_match.group(1), base)

        for match in re.finditer(
            r"\bindex\s*:\s*true\s*,[\s\S]{0,180}?element\s*:\s*<\s*([A-Z][A-Za-z0-9_]+)",
            text,
        ):
            add(match.group(1), base or "/", base)
    return route_map


def route_for_file(path: Path, root: Path, framework: str, route_map: dict[str, list[str]] | None = None) -> str | None:
    routes = routes_for_file(path, root, framework, route_map)
    return routes[0] if routes else None


def routes_for_file(
    path: Path,
    root: Path,
    framework: str,
    route_map: dict[str, list[str]] | None = None,
) -> list[str]:
    rel = relpath(path, root)
    name = path.name
    lower = name.lower()
    if framework == "next-app":
        if (rel.startswith("app/") or "/app/" in rel) and name.split(".")[0] in ("page", "route"):
            route = route_from_next_app(rel)
            return [route] if route else []
        return []
    if framework == "next-pages":
        if rel.startswith("pages/") and path.suffix.lower() in (".js", ".jsx", ".ts", ".tsx"):
            if lower.startswith("_") or rel.startswith("pages/api/"):
                return []
            return [route_from_pages(rel, "pages/")]
        return []
    if framework == "nuxt":
        if rel.startswith("pages/") and path.suffix.lower() == ".vue":
            return [route_from_pages(rel, "pages/")]
        return []
    if framework == "sveltekit":
        if name.startswith("+page.") and name.endswith(".svelte"):
            return [route_from_pages(rel, "src/routes/").replace("+page", "")]
        return []
    if framework == "astro":
        if rel.startswith("src/pages/") and path.suffix.lower() in (".astro", ".md", ".mdx"):
            return [route_from_pages(rel, "src/pages/")]
        return []
    if framework == "remix":
        if rel.startswith("app/routes/"):
            return [route_from_remix(rel)]
        return []
    if framework == "vite-spa":
        if path.parent.name == "pages" and path.suffix.lower() in (".jsx", ".tsx", ".js", ".ts", ".vue", ".svelte"):
            mapped = (route_map or {}).get(path.stem)
            if mapped:
                return list(mapped)
            if path.stem.lower() in ("home", "index"):
                return ["/"]
            return []
        if path.suffix.lower() in (".html", ".htm") and lower not in ("404.html", "404.htm"):
            if path.parent == root or rel.startswith("gastronomie/"):
                return [route_from_static(rel)]
        return []
    if framework == "static":
        if rel.startswith("public/"):
            return []
        if path.suffix.lower() in (".html", ".htm") and lower not in ("404.html", "404.htm"):
            return [route_from_static(rel)]
        return []
    if framework in ("django", "flask", "fastapi", "rails"):
        if any(part in rel for part in ("templates/", "app/views/")) and path.suffix.lower() in (".html", ".htm", ".jinja", ".jinja2", ".j2", ".erb", ".twig"):
            return ["/" + re.sub(r"\.(html?|jinja2?|j2|erb|twig)$", "", rel, flags=re.I).split("templates/")[-1].split("app/views/")[-1].strip("/")]
        return []
    if framework == "wordpress":
        if path.suffix.lower() == ".php" and (lower.startswith(("page-", "single-", "archive-", "index", "front-page", "home"))):
            return ["/" + re.sub(r"\.php$", "", rel, flags=re.I)]
        return []
    return []


def is_layout_file(path: Path, framework: str) -> bool:
    rel = relpath(path, Path(".")).lower()
    name = path.name.lower()
    if framework == "next-app" and name.startswith("layout."):
        return True
    if framework == "next-pages" and name in ("_app.js", "_app.jsx", "_app.tsx", "_document.js", "_document.jsx", "_document.tsx"):
        return True
    if framework == "sveltekit" and name.startswith("+layout."):
        return True
    if framework == "nuxt" and name in ("app.vue", "layouts/default.vue"):
        return True
    if framework == "astro" and ("layout" in name or "base" in name):
        return True
    if framework == "remix" and name == "root.tsx":
        return True
    return any(part in rel for part in ("layout.", "base.html", "shell."))


def is_root_layout_file(rel: str, name: str, framework: str) -> bool:
    rel = rel.lower().replace("\\", "/")
    if framework == "next-app":
        return bool(re.match(r"(?:.*/)?(?:src/)?app/layout\.[a-z]+$", rel))
    if framework == "next-pages":
        return name in ("_app.js", "_app.jsx", "_app.tsx", "_document.js", "_document.jsx", "_document.tsx")
    if framework == "sveltekit":
        return bool(re.match(r"(?:.*/)?(?:src/routes/)?\+layout\.svelte$", rel))
    if framework == "nuxt":
        return rel.endswith("app.vue") or rel.endswith("layouts/default.vue")
    if framework == "remix":
        return rel.endswith("root.tsx")
    return False


PRIVATE_SEGMENTS = {
    "admin", "account", "dashboard", "login", "signin", "sign-in",
    "preview", "unsubscribe", "confirm", "checkout", "cart", "auth",
}


def is_private_route(route: str) -> bool:
    parts = [part for part in route.strip("/").split("/") if part]
    return any(part.lower() in PRIVATE_SEGMENTS for part in parts)


def is_email_template(rel: str) -> bool:
    value = "/" + rel.lower().replace("\\", "/")
    return any(
        marker in value
        for marker in ("/email_templates/", "/email-templates/", "/templates/email/", "/mail/templates/", "/emails/")
    )


def parse_gitmodules(root: Path) -> list[dict[str, str]]:
    text = read_text(root / ".gitmodules")
    modules: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[submodule"):
            if current:
                modules.append(current)
            current = {}
        elif "=" in stripped:
            key, value = stripped.split("=", 1)
            current[key.strip()] = value.strip()
    if current:
        modules.append(current)
    return [
        {"name": item.get("path", "").strip("/").split("/")[-1] or "submodule",
         "path": item.get("path", ""), "url": item.get("url", "")}
        for item in modules if item.get("path")
    ]


def readme_text(root: Path) -> str:
    for name in ("README.md", "readme.md", "README.txt"):
        path = root / name
        if path.exists():
            return read_text(path)[:8000]
    return ""


def detect_build_context(root: Path) -> dict[str, Any]:
    """Find build/sitemap/prerender artefacts around an app root.

    Vite monorepos often keep the sitemap generator, prerender script and route
    registry one level above the SPA (``frontend/scripts`` for
    ``frontend/website``). Looking only inside the app root creates false
    ``sitemap-missing`` / ``csr-only`` findings.
    """
    context: dict[str, Any] = {
        "sitemap": False,
        "prerender": False,
        "robots": False,
        "not_found": False,
        "built_html": False,
        "hreflang_in_sitemap": False,
        "route_registry": False,
        "evidence": [],
    }
    parent = root.parent
    app_slug = root.name.lower()
    package = read_json(parent / "package.json") if parent != root else {}
    scripts = package.get("scripts") or {}
    relevant_scripts = {
        key: value for key, value in scripts.items()
        if app_slug in key.lower()
    }
    if not relevant_scripts and len(scripts) <= 3:
        relevant_scripts = scripts
    script_text = " ".join(str(value) for value in relevant_scripts.values()).lower()
    if "sitemap" in script_text:
        context["sitemap"] = True
        context["evidence"].append(str(parent / "package.json"))
    if "prerender" in script_text:
        context["prerender"] = True
        context["evidence"].append(str(parent / "package.json"))

    script_dirs = [parent / "scripts", parent / "scripts" / "lib", root / "scripts"]
    for directory in script_dirs:
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.js")) + sorted(directory.glob("*.mjs")) + sorted(directory.glob("*.ts")):
            lower_name = path.name.lower()
            if app_slug not in lower_name and not (app_slug == "website" and "website" in lower_name):
                continue
            text = read_text(path)
            if "sitemap" in lower_name or "sitemap" in text.lower():
                context["sitemap"] = True
                context["evidence"].append(str(path))
                if "hreflang" in text.lower() or "alternatesfor" in text.lower():
                    context["hreflang_in_sitemap"] = True
            if "prerender" in lower_name or "prerender" in text.lower():
                context["prerender"] = True
                context["evidence"].append(str(path))
            if "website-routes" in lower_name or "route-registry" in lower_name:
                context["route_registry"] = True
                context["evidence"].append(str(path))

    built_roots = [root] if root.name.lower() in ("dist", "build", "out") else []
    built_roots += [root / "dist", root / "build", root / "out", root.parent / "dist"]
    for built_root in built_roots:
        if (built_root / "index.html").exists():
            context["built_html"] = True
        if (built_root / "sitemap.xml").exists():
            context["sitemap"] = True
        if (built_root / "robots.txt").exists():
            context["robots"] = True
        if (built_root / "404.html").exists():
            context["not_found"] = True
        if context["built_html"]:
            break
    public = root / "public"
    if (public / "robots.txt").exists():
        context["robots"] = True
    if (root / "robots.txt").exists():
        context["robots"] = True
    if (root / "sitemap.xml").exists() or (root / "public" / "sitemap.xml").exists():
        context["sitemap"] = True
    for rel in ("404.html", "not-found.tsx", "not-found.jsx", "src/not-found.tsx",
                "src/pages/NotFound.jsx", "src/pages/NotFound.tsx", "app/not-found.tsx"):
        if (root / rel).exists():
            context["not_found"] = True
            break
    return context


def discover_apps(root: Path, files: list[Path]) -> list[dict[str, Any]]:
    """Build a lightweight warehouse of app/service roots for umbrella repos."""
    candidates: dict[str, dict[str, Any]] = {}

    def add(path: Path, kind: str, evidence: str) -> None:
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            return
        if rel in ("", "."):
            rel = "."
        current = candidates.setdefault(rel, {"path": rel, "kind": kind, "evidence": []})
        if evidence and evidence not in current["evidence"]:
            current["evidence"].append(evidence)
        if kind in ("frontend", "backend") and current["kind"] in ("unknown", "submodule"):
            current["kind"] = kind

    for module in parse_gitmodules(root):
        add(root / module["path"], "submodule", module.get("url", ""))

    for path in files:
        name = path.name.lower()
        parent = path.parent
        if name in ("vite.config.js", "vite.config.ts", "next.config.js", "next.config.mjs",
                    "next.config.ts", "astro.config.mjs", "astro.config.ts", "nuxt.config.ts",
                    "nuxt.config.js", "svelte.config.js", "angular.json"):
            add(parent, "frontend", relpath(path, root))
        elif name == "package.json":
            data = read_json(path)
            deps = {** (data.get("dependencies") or {}), ** (data.get("devDependencies") or {})}
            if any(key in deps for key in ("vite", "next", "nuxt", "astro", "@sveltejs/kit", "@angular/core", "@remix-run/react")):
                add(parent, "frontend", relpath(path, root))
            elif data.get("scripts") and parent != root:
                add(parent, "tool", relpath(path, root))
        elif name in ("requirements.txt", "pyproject.toml"):
            add(parent, "backend", relpath(path, root))
        elif name in ("app.py", "main.py", "asgi.py") and parent != root:
            add(parent, "backend", relpath(path, root))
        elif name == "index.html" and parent != root:
            # An app shell below the root; avoid deep public asset folders.
            rel = relpath(parent, root)
            if rel.count("/") <= 2 and not any(part in rel.lower() for part in ("public/", "static/", "mock", "fixture")):
                add(parent, "frontend", relpath(path, root))
        elif name in ("agents.md", "readme.md", "todo.md"):
            rel = relpath(parent, root)
            if rel != "." and rel.count("/") <= 1 and parent.name.lower() in (
                "docs", "business", "marketing", "plans", "strategy", "social",
            ):
                add(parent, "docs", relpath(path, root))

    apps: list[dict[str, Any]] = []
    for item in sorted(candidates.values(), key=lambda value: value["path"]):
        apps.append(item)
    return apps


def classify_scope(
    root: Path,
    files: list[Path],
    framework: str,
    routes_count: int,
    package_files: list[str],
    build: dict[str, Any],
    override: str = "auto",
) -> tuple[str, str]:
    rels = [relpath(path, root).lower() for path in files]
    name = root.name.lower()
    readme = readme_text(root).lower()
    index_text = read_text(root / "index.html").lower()
    robots_text = read_text(root / "robots.txt").lower()
    if not robots_text:
        robots_text = read_text(root / "public" / "robots.txt").lower()
    md_files = [rel for rel in rels if rel.endswith((".md", ".mdx"))]
    docs_ratio = len(md_files) / max(1, len(rels))
    internal_name = any(
        segment in name.split("-") or name == segment
        for segment in ("admin", "dashboard", "backoffice", "internal", "console", "staff", "ops")
    )

    if override in ("public", "internal", "context"):
        return override, ""
    if (root / ".gitmodules").exists():
        return "umbrella", "Umbrella repository with submodules. Scan each app root separately; the root is not a site."
    package_data = read_json(root / "package.json")
    package_scripts = package_data.get("scripts") or {}
    script_blob = " ".join(str(value) for value in package_scripts.values()).lower()
    if routes_count == 0 and ("build:all" in script_blob or "dev:all" in script_blob or package_data.get("workspaces")):
        return "umbrella", "Multi-app root without routes. Scan each app folder (for example frontend/site) separately."
    if docs_ratio >= 0.45 and not package_files and routes_count == 0:
        return "docs", "Documentation/context repository; it has no public web routes and is not scored as a website."
    if (
        routes_count == 0
        and not (root / "package.json").exists()
        and not (root / "requirements.txt").exists()
        and not (root / "pyproject.toml").exists()
        and len(md_files) >= 8
    ):
        return "docs", "Documentation/context repository; it has no public web routes and is not scored as a website."
    if "127.0.0.1" in readme and any(word in readme for word in ("lokal", "local", "eine person", "single user", "nur für diesen workspace")):
        return "local-tool", "Local-only tool (README binds it to 127.0.0.1); it is not a public website."
    if not index_text and robots_text and re.search(r"(?im)^\s*disallow:\s*/\s*$", robots_text):
        return "internal", "Internal app with robots.txt blocking all crawlers; marketing rules are not applicable."
    if "noindex" in index_text and "nofollow" in index_text:
        return "internal", "Internal app shell with noindex,nofollow; only accidental indexability is relevant."
    if internal_name and routes_count:
        return "internal", "Internal app by name/path; marketing SEO rules are not applicable."
    if framework in ("django", "flask", "fastapi", "rails") and routes_count == 0:
        return "backend", "Backend service without public HTML routes; pair it with its frontend app and use live checks."
    if framework in (
        "next-app", "next-pages", "nuxt", "sveltekit", "astro", "remix", "vite-spa", "angular",
    ) and package_files:
        return "public", ""
    if routes_count > 0 or build.get("built_html") or build.get("route_registry"):
        return "public", ""
    if docs_ratio >= 0.45:
        return "docs", "Documentation/context repository without public web routes."
    return "unknown", "No public routes detected; verify the scan root before using this report."


def context_sources(root: Path) -> list[str]:
    wanted = (
        "AGENTS.md", "README.md", "TODO.md", "strategy/entscheidungen.md",
        "strategy/seitenarchitektur.md", "marketing/TODO.md", "marketing/AGENTS.md",
    )
    found: list[str] = []
    for rel in wanted:
        if (root / rel).exists():
            found.append(rel)
    for path in sorted(root.glob("strategy/*.md")):
        rel = relpath(path, root)
        if rel not in found:
            found.append(rel)
    return found[:10]


def extract_jsonld(blocks: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    parsed: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, block in enumerate(blocks, 1):
        try:
            value = json.loads(block)
        except json.JSONDecodeError as exc:
            errors.append(f"block {index}: {exc}")
            continue
        items = value if isinstance(value, list) else [value]
        for item in items:
            if isinstance(item, dict):
                parsed.append(item)
    return parsed, errors


def collect_jsonld_types(items: list[dict[str, Any]]) -> list[str]:
    found: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            type_value = value.get("@type")
            if isinstance(type_value, str):
                found.append(type_value)
            elif isinstance(type_value, list):
                found.extend(str(item) for item in type_value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    for item in items:
        walk(item)
    return sorted(set(found))


def extract_metadata(text: str, framework: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "titles": [],
        "descriptions": [],
        "canonicals": [],
        "robots": [],
        "h1": [],
        "h1_count": 0,
        "has_metadata_api": False,
        "has_og": False,
        "has_twitter": False,
        "has_jsonld": False,
        "jsonld_blocks": [],
        "jsonld_errors": [],
        "jsonld_types": [],
        "images": [],
        "anchors": [],
        "stylesheet_links": 0,
        "blocking_scripts": [],
        "google_fonts": False,
        "hreflang": [],
    }

    for match in re.finditer(r"<title[^>]*>(.*?)</title>", text, re.I | re.S):
        result["titles"].append(clean_text(match.group(1)))
    for match in re.finditer(r"<meta\b[^>]*>", text, re.I | re.S):
        tag = match.group(0)
        name = re.search(r"\bname\s*=\s*['\"]([^'\"]+)['\"]", tag, re.I)
        prop = re.search(r"\bproperty\s*=\s*['\"]([^'\"]+)['\"]", tag, re.I)
        content = re.search(r"\bcontent\s*=\s*['\"]([^'\"]*)['\"]", tag, re.I)
        key = (name.group(1) if name else prop.group(1) if prop else "").lower()
        value = content.group(1) if content else ""
        if key == "description":
            result["descriptions"].append(clean_text(value))
        elif key == "robots":
            result["robots"].append(value)
        elif key.startswith("og:"):
            result["has_og"] = True
        elif key.startswith("twitter:"):
            result["has_twitter"] = True
    for match in re.finditer(r"<link\b[^>]*>", text, re.I | re.S):
        tag = match.group(0)
        rel = re.search(r"\brel\s*=\s*['\"]([^'\"]+)['\"]", tag, re.I)
        href = re.search(r"\bhref\s*=\s*['\"]([^'\"]+)['\"]", tag, re.I)
        hreflang = re.search(r"\bhreflang\s*=\s*['\"]([^'\"]+)['\"]", tag, re.I)
        rel_value = (rel.group(1) if rel else "").lower()
        if "canonical" in rel_value and href:
            result["canonicals"].append(href.group(1))
        if "stylesheet" in rel_value:
            result["stylesheet_links"] += 1
        if hreflang and href:
            result["hreflang"].append({"hreflang": hreflang.group(1), "href": href.group(1)})
    for match in re.finditer(r"<h1\b[^>]*>(.*?)</h1>", text, re.I | re.S):
        result["h1"].append(clean_text(match.group(1)))
    result["h1_count"] = len(result["h1"])

    for match in re.finditer(r"<img\b[^>]*>", text, re.I | re.S):
        tag = match.group(0)
        attrs = {
            key.lower(): (value or "")
            for key, value in re.findall(r"([A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*['\"]([^'\"]*)['\"]", tag)
        }
        result["images"].append({"tag": tag, "attrs": attrs, "line": line_of(text, match)})
    for match in re.finditer(r"<a\b([^>]*)>(.*?)</a>", text, re.I | re.S):
        attrs_raw, inner = match.group(1), match.group(2)
        href_match = re.search(
            r"\bhref\s*=\s*(?:['\"]([^'\"]*)['\"]|\{([^}]*)\})", attrs_raw, re.I
        )
        dynamic = bool(href_match and href_match.group(1) is None and href_match.group(2) is not None)
        result["anchors"].append(
            {
                "href": href_match.group(1) if href_match and href_match.group(1) is not None else "",
                "dynamic": dynamic,
                "text": clean_text(inner),
                "line": line_of(text, match),
            }
        )
    for match in re.finditer(r"<script\b([^>]*)>(.*?)</script>", text, re.I | re.S):
        attrs = match.group(1)
        if re.search(r"\btype\s*=\s*['\"]application/ld\+json['\"]", attrs, re.I):
            result["has_jsonld"] = True
            result["jsonld_blocks"].append(match.group(2).strip())
        src = re.search(r"\bsrc\s*=\s*['\"]([^'\"]+)['\"]", attrs, re.I)
        if src and not re.search(r"\b(defer|async)\b", attrs, re.I) and not re.search(r"\btype\s*=\s*['\"]module['\"]", attrs, re.I):
            result["blocking_scripts"].append(src.group(1))
    if "fonts.googleapis.com" in text or "fonts.gstatic.com" in text:
        result["google_fonts"] = True

    if framework.startswith("next"):
        result["has_metadata_api"] = bool(re.search(r"\bexport\s+const\s+metadata\b|\bgenerateMetadata\b", text))
        for match in re.finditer(r"\btitle\s*:\s*(['\"`])(.*?)\1", text, re.S):
            result["titles"].append(clean_text(match.group(2)))
        for match in re.finditer(r"\bdescription\s*:\s*(['\"`])(.*?)\1", text, re.S):
            result["descriptions"].append(clean_text(match.group(2)))
        for match in re.finditer(r"\b(?:canonical|url)\s*:\s*(['\"`])(.*?)\1", text, re.S):
            candidate = match.group(2)
            if candidate.startswith(("http://", "https://", "/")):
                result["canonicals"].append(candidate)
        if re.search(r"\brobots\s*:\s*\{[^}]*\bindex\s*:\s*false", text, re.S | re.I):
            result["robots"].append("noindex")
    elif framework == "nuxt":
        result["has_metadata_api"] = bool(re.search(r"\buseSeoMeta\b|\buseHead\b|\bdefinePageMeta\b|\bapp\s*:\s*\{[^}]*head", text, re.S))
        for match in re.finditer(r"\b(title|description|ogTitle|ogDescription)\s*:\s*(['\"`])(.*?)\2", text, re.S):
            key = match.group(1)
            if key == "title":
                result["titles"].append(clean_text(match.group(3)))
            elif key == "description":
                result["descriptions"].append(clean_text(match.group(3)))
        for match in re.finditer(r"\b(?:canonical|href)\s*:\s*(['\"`])(.*?)\1", text, re.S):
            candidate = match.group(2)
            if candidate.startswith(("http://", "https://", "/")):
                result["canonicals"].append(candidate)
        if re.search(r"\brobots\s*:\s*['\"][^'\"]*noindex", text, re.I):
            result["robots"].append("noindex")
    elif framework == "sveltekit":
        for block in re.finditer(r"<svelte:head>(.*?)</svelte:head>", text, re.I | re.S):
            inner = block.group(1)
            result["has_metadata_api"] = True
            for match in re.finditer(r"<title[^>]*>(.*?)</title>", inner, re.I | re.S):
                result["titles"].append(clean_text(match.group(1)))
            for match in re.finditer(r"<meta\b[^>]*name=['\"]description['\"][^>]*content=['\"]([^'\"]*)", inner, re.I):
                result["descriptions"].append(clean_text(match.group(1)))
            for match in re.finditer(r"<link\b[^>]*rel=['\"]canonical['\"][^>]*href=['\"]([^'\"]*)", inner, re.I):
                result["canonicals"].append(match.group(1))
        if "svelte:head" in text:
            result["has_metadata_api"] = True
    elif framework == "remix":
        result["has_metadata_api"] = bool(re.search(r"\bexport\s+(?:const|function)\s+meta\b", text))
        for match in re.finditer(r"\btitle\s*:\s*(['\"`])(.*?)\1", text, re.S):
            result["titles"].append(clean_text(match.group(2)))
        for match in re.finditer(r"\bname\s*:\s*['\"]description['\"]\s*,\s*content\s*:\s*(['\"`])(.*?)\1", text, re.S):
            result["descriptions"].append(clean_text(match.group(2)))
        for match in re.finditer(r"\btagName\s*:\s*['\"]link['\"][^}]*\brel\s*:\s*['\"]canonical['\"][^}]*\bhref\s*:\s*(['\"`])(.*?)\1", text, re.S):
            result["canonicals"].append(match.group(2))
    elif framework == "astro":
        for match in re.finditer(r"\b(title|description)\s*[:=]\s*(['\"`])(.*?)\2", text, re.S):
            key = match.group(1)
            if key == "title":
                result["titles"].append(clean_text(match.group(3)))
            elif key == "description":
                result["descriptions"].append(clean_text(match.group(3)))
        if "<title>" in text:
            result["has_metadata_api"] = True
    elif framework in ("vite-spa", "unknown"):
        for match in re.finditer(r"\b(?:useMeta|useSeoMeta|useHead|Helmet)\s*\(\s*\{(.*?)\}\s*\)", text, re.S):
            block = match.group(1)
            result["has_metadata_api"] = True
            title = re.search(r"\btitle\s*:\s*(['\"`])(.*?)\1", block, re.S)
            description = re.search(r"\bdescription\s*:\s*(['\"`])(.*?)\1", block, re.S)
            canonical = re.search(r"\bcanonical\s*:\s*(['\"`])(.*?)\1", block, re.S)
            if title:
                result["titles"].append(clean_text(title.group(2)))
            if description:
                result["descriptions"].append(clean_text(description.group(2)))
            if canonical:
                result["canonicals"].append(canonical.group(2))
        if re.search(r"react-helmet|useMeta|useSeoMeta", text):
            result["has_metadata_api"] = True


    parsed, errors = extract_jsonld(result["jsonld_blocks"])
    result["jsonld_errors"] = errors
    result["jsonld_types"] = collect_jsonld_types(parsed)
    result["jsonld_items"] = parsed
    return result


def analyze_schema(items: list[dict[str, Any]], path: Path, rel: str, issues: list[dict[str, Any]]) -> None:
    for item in items:
        type_value = item.get("@type")
        types = type_value if isinstance(type_value, list) else [type_value]
        types = [str(value) for value in types if value]
        if any(value in ("Article", "NewsArticle", "BlogPosting") for value in types):
            missing = [key for key in ("headline", "image", "datePublished", "author") if key not in item]
            if missing:
                add_issue(
                    issues, "schema-article-fields", "low", "structured-data",
                    "Article/NewsArticle JSON-LD is missing recommended fields: " + ", ".join(missing) + ".",
                    rel, 0, {"types": types, "missing": missing},
                    "Add the missing fields when they are true for the page; keep JSON-LD identical to visible content.",
                    "likely",
                )
        if "Product" in types:
            offers = item.get("offers")
            missing = []
            if not item.get("name"):
                missing.append("name")
            if not offers:
                missing.append("offers")
            if missing:
                add_issue(
                    issues, "schema-product-fields", "medium", "structured-data",
                    "Product JSON-LD is missing required fields: " + ", ".join(missing) + ".",
                    rel, 0, {"types": types, "missing": missing},
                    "Add name and offers (price, priceCurrency, availability) only when they match the page.",
                    "likely",
                )
        if "LocalBusiness" in types:
            missing = [key for key in ("name", "address") if key not in item]
            if missing:
                add_issue(
                    issues, "schema-localbusiness-fields", "medium", "structured-data",
                    "LocalBusiness JSON-LD is missing required fields: " + ", ".join(missing) + ".",
                    rel, 0, {"types": types, "missing": missing},
                    "Add name and PostalAddress; keep NAP consistent with the visible page.",
                    "likely",
                )
        if "FAQPage" in types:
            main = item.get("mainEntity")
            if not isinstance(main, list) or not main:
                add_issue(
                    issues, "schema-faq-fields", "medium", "structured-data",
                    "FAQPage JSON-LD has no mainEntity questions.",
                    rel, 0, {"types": types},
                    "Mark up visible questions and answers; do not invent FAQs.",
                    "likely",
                )


def analyze_route(
    path: Path,
    root: Path,
    rel: str,
    route: str,
    text: str,
    framework: str,
    issues: list[dict[str, Any]],
    routes: list[dict[str, Any]],
    private_route: bool = False,
    layout_defaults: bool = False,
    static_export: bool = False,
) -> None:
    meta = extract_metadata(text, framework)
    route_entry: dict[str, Any] = {
        "route": route,
        "file": rel,
        "title": meta["titles"][0] if meta["titles"] else "",
        "description": meta["descriptions"][0] if meta["descriptions"] else "",
        "canonical": meta["canonicals"][0] if meta["canonicals"] else "",
        "h1_count": meta["h1_count"],
        "h1": meta["h1"][0] if meta["h1"] else "",
        "has_metadata_api": meta["has_metadata_api"],
        "has_jsonld": meta["has_jsonld"],
        "jsonld_types": ";".join(meta["jsonld_types"]),
        "images": len(meta["images"]),
        "noindex": any("noindex" in value.lower() for value in meta["robots"]),
        "private": private_route,
    }
    routes.append(route_entry)

    if not private_route and not route_entry["noindex"]:
        visible = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
        visible = re.sub(r"/\*.*?\*/", " ", visible, flags=re.S)
        visible = re.sub(r"(?m)^\s*//.*$", " ", visible)
        marker = DRAFT_MARKERS.search(visible)
        if marker:
            add_issue(
                issues, "draft-indexable", "low", "content",
                "Draft/placeholder content is indexable.",
                rel, line_of(visible, marker), {"route": route, "marker": marker.group(0)},
                "Add noindex until the page is finished and keep it out of the sitemap; do not publish drafts.",
                "likely",
            )

    if not meta["titles"] and not private_route:
        runtime_meta = meta["has_metadata_api"]
        dynamic_meta = framework == "astro" or layout_defaults or runtime_meta
        severity = "info" if dynamic_meta else ("high" if framework == "static" else "medium")
        if framework == "astro":
            suffix = " Astro pages often pass metadata as layout props or from a content collection; verify the built HTML."
        elif runtime_meta:
            suffix = " A runtime metadata hook (useMeta/Helmet/useHead) is present; verify the built or rendered HTML."
        elif layout_defaults:
            suffix = " The root layout may provide a default; verify the built HTML."
        else:
            suffix = ""
        add_issue(
            issues, "title-missing-in-route", severity,
            "on-page", "No title found in this route file." + suffix,
            rel, line_of(text, text.find("metadata") if "metadata" in text else 0), {"route": route},
            "Add a unique title in the route metadata or the page head; check whether a layout provides a safe default.",
            "likely" if framework != "static" else "confirmed",
        )
    else:
        title = meta["titles"][0] if meta["titles"] else ""
        if title.strip().lower() in GENERIC_TITLES:
            add_issue(
                issues, "title-generic", "high", "on-page",
                f"Generic title: {title!r}.",
                rel, line_of(text, text.find(title)), {"title": title},
                "Replace it with a page-specific title that names the topic and, if useful, the brand.",
                "confirmed",
            )
        if len(title) > 65:
            add_issue(
                issues, "title-long", "low", "on-page",
                f"Title is {len(title)} characters; it may be truncated in search results.",
                rel, line_of(text, text.find(title)), {"title": title},
                "Move the distinguishing information to the front; keep the brand short.",
                "confirmed",
            )

    if not meta["descriptions"] and not private_route:
        runtime_meta = meta["has_metadata_api"]
        dynamic_meta = framework == "astro" or layout_defaults or runtime_meta
        severity = "info" if dynamic_meta else ("low" if framework != "static" else "medium")
        if framework == "astro":
            suffix = " Astro pages often pass metadata as layout props or from a content collection; verify the built HTML."
        elif runtime_meta:
            suffix = " A runtime metadata hook (useMeta/Helmet/useHead) is present; verify the built or rendered HTML."
        elif layout_defaults:
            suffix = " The root layout may provide a default; verify the built HTML."
        else:
            suffix = ""
        add_issue(
            issues, "description-missing-in-route", severity,
            "on-page", "No meta description found in this route file." + suffix,
            rel, 0, {"route": route},
            "Add a unique, human-readable summary where the route controls its metadata; a layout default is not a substitute for money pages.",
            "likely" if framework != "static" else "confirmed",
        )
    elif meta["descriptions"] and len(meta["descriptions"][0]) > 170:
        add_issue(
            issues, "description-long", "low", "on-page",
            f"Meta description is {len(meta['descriptions'][0])} characters.",
            rel, 0, {"description": meta["descriptions"][0]},
            "Put the main point in the first 120-160 characters; Google may truncate or rewrite it.",
            "confirmed",
        )

    hero_component = bool(
        re.search(r"<[A-Z][A-Za-z0-9_]*Hero\b", text)
        or re.search(r"<Hero(?:Section)?\b", text)
    )
    if meta["h1_count"] == 0 and not private_route:
        severity = "info" if hero_component else ("medium" if framework == "static" else "low")
        message = (
            "No H1 in this route file; an imported Hero component receives the title and likely renders it. Verify the built HTML."
            if hero_component
            else "No H1 found in this route file; it may be rendered by an imported component."
        )
        add_issue(
            issues, "h1-missing-in-route", severity, "on-page",
            message,
            rel, 0, {"route": route, "hero_component": hero_component},
            "Verify the rendered page. If no component renders an H1, add one descriptive H1; keep exactly one in the final page.",
            "likely",
        )
    elif meta["h1_count"] > 1 and not private_route:
        add_issue(
            issues, "h1-multiple-in-route", "medium", "on-page",
            f"{meta['h1_count']} H1 elements found in this route file.",
            rel, 0, {"h1": meta["h1"]},
            "Keep one H1 per rendered page; demote the others to H2/H3.",
            "confirmed",
        )

    for image in meta["images"]:
        attrs = image["attrs"]
        tag = image["tag"]
        image_hero = bool(re.search(r"hero", tag, re.I))
        dynamic_attr = lambda name: bool(re.search(rf"\b{name}\s*=\s*\{{", tag))  # noqa: E731
        if "alt" not in attrs and not dynamic_attr("alt"):
            add_issue(
                issues, "image-alt-missing", "medium", "media",
                "Image has no alt attribute.",
                rel, image["line"], {"tag": image["tag"][:180]},
                "Describe the image's purpose; use alt=\"\" only for decorative images.",
                "confirmed",
            )
        if (not attrs.get("width") or not attrs.get("height")) and not dynamic_attr("width") and not dynamic_attr("height"):
            add_issue(
                issues, "image-dimensions-missing", "low", "media",
                "Image has no width/height attributes.",
                rel, image["line"], {"tag": image["tag"][:180]},
                "Set intrinsic dimensions or an aspect ratio to avoid layout shift.",
                "confirmed",
            )
        if attrs.get("loading", "").lower() == "lazy" and image is meta["images"][0] and not private_route:
            severity = "medium" if image_hero else "info"
            message = (
                "The first image uses loading=\"lazy\"; it may be the LCP element."
                if image_hero
                else "The first image uses loading=\"lazy\"; its above-the-fold position was not verified."
            )
            add_issue(
                issues, "lcp-image-lazy", severity, "performance",
                message,
                rel, image["line"], {"tag": image["tag"][:180], "hero_context": image_hero},
                "Do not lazy-load the hero/LCP image; use eager loading and fetchpriority=\"high\" when appropriate.",
                "likely",
            )

    for anchor in meta["anchors"]:
        if anchor.get("dynamic"):
            continue
        if anchor["href"] in ("#", "", "javascript:void(0)", "javascript:;"):
            add_issue(
                issues, "link-not-crawlable", "medium", "internal-linking",
                "Anchor has no crawlable destination.",
                rel, anchor["line"], {"href": anchor["href"], "text": anchor["text"][:80]},
                "Use a real <a href> to a crawlable URL; do not rely on click handlers for navigation.",
                "confirmed",
            )
        elif anchor["text"].strip().lower() in GENERIC_ANCHORS:
            add_issue(
                issues, "anchor-text-generic", "low", "internal-linking",
                f"Generic anchor text: {anchor['text']!r}.",
                rel, anchor["line"], {"href": anchor["href"], "text": anchor["text"][:80]},
                "Use descriptive anchor text that names the destination.",
                "confirmed",
            )

    if meta["jsonld_errors"]:
        add_issue(
            issues, "jsonld-invalid", "medium", "structured-data",
            "JSON-LD block is not valid JSON.",
            rel, 0, {"errors": meta["jsonld_errors"]},
            "Fix the JSON syntax and validate it with the Rich Results Test.",
            "confirmed",
        )
    analyze_schema(meta.get("jsonld_items", []), path, rel, issues)

    if re.search(r"['\"]use client['\"]", text[:300]):
        severity = "info" if static_export else "high"
        note = " Static export detected; verify the built HTML contains the content." if static_export else ""
        add_issue(
            issues, "client-page", severity, "rendering",
            "Route file is marked as a client component." + note,
            rel, line_of(text, re.search(r"['\"]use client['\"]", text[:300]) or 0),
            {"route": route, "framework": framework, "static_export": static_export},
            "Keep public content in a server component or render the primary content on the server; use client components only for interactive islands.",
            "likely",
        )
    if re.search(r"\bexport\s+const\s+ssr\s*=\s*false\b", text):
        add_issue(
            issues, "ssr-disabled", "high", "rendering",
            "SSR is explicitly disabled for this route or layout.",
            rel, line_of(text, re.search(r"\bexport\s+const\s+ssr\s*=\s*false\b", text) or 0),
            {"route": route},
            "Remove the override for public, indexable pages; keep SSR for content that must be in the initial HTML.",
            "confirmed",
        )
    if re.search(r"\bssr\s*:\s*false\b|\bdynamic\s*\([^)]*ssr\s*:\s*false", text):
        add_issue(
            issues, "ssr-disabled", "high", "rendering",
            "SSR appears to be disabled via configuration or dynamic import.",
            rel, line_of(text, re.search(r"\bssr\s*:\s*false\b|\bdynamic\s*\([^)]*ssr\s*:\s*false", text) or 0),
            {"route": route},
            "Render public content on the server; keep client-only loading for logged-in/app screens.",
            "likely",
        )
    if re.search(r"client:only", text):
        add_issue(
            issues, "client-only-island", "medium", "rendering",
            "Astro client:only island renders no HTML on the server.",
            rel, line_of(text, re.search(r"client:only", text) or 0),
            {"route": route},
            "Use client:load or server-render the component when its text or links must be indexable.",
            "likely",
        )


def analyze_global_file(
    path: Path,
    rel: str,
    text: str,
    framework: str,
    issues: list[dict[str, Any]],
    is_global: bool = True,
) -> None:
    meta = extract_metadata(text, framework)
    if is_global and meta["titles"] and meta["titles"][0].strip().lower() in GENERIC_TITLES:
        add_issue(
            issues, "title-generic", "high", "on-page",
            f"Shared layout uses a generic title: {meta['titles'][0]!r}.",
            rel, 0, {"title": meta["titles"][0]},
            "Use a real default title and a per-page title template; do not let every route inherit \"Home\".",
            "confirmed",
        )
    if is_global and re.search(r"\bnoindex\b", " ".join(meta["robots"]).lower()):
        add_issue(
            issues, "global-noindex", "critical", "indexing",
            "Global layout/template contains a noindex directive.",
            rel, 0, {"robots": meta["robots"]},
            "Remove noindex from the shared layout; apply it only to pages that must stay out of search.",
            "confirmed",
        )
    if is_global and meta["canonicals"]:
        canonical = meta["canonicals"][0]
        if not any(token in canonical for token in ("${", "{{", "%s")):
            add_issue(
                issues, "global-canonical", "low", "indexing",
                f"Root layout sets a canonical default: {canonical}. Every indexable route must override it.",
                rel, 0, {"canonical": canonical},
                "Generate the canonical per route from the request URL or route data; verify each public route overrides the default.",
                "likely",
            )
    if is_global and meta["h1_count"] > 0 and is_layout_file(path, framework):
        add_issue(
            issues, "h1-in-layout", "medium", "on-page",
            f"{meta['h1_count']} H1 element(s) found in a shared layout/header.",
            rel, 0, {"h1": meta["h1"]},
            "Use a non-heading element for the logo/site name, or ensure the layout does not add a second H1 to every page.",
            "likely",
        )
    if is_global and meta["google_fonts"]:
        add_issue(
            issues, "third-party-fonts", "low", "performance",
            "Page loads fonts from Google Fonts.",
            rel, 0, {},
            "Self-host the fonts or preconnect/preload them; third-party font requests add latency and a privacy dependency.",
            "confirmed",
        )
    if is_global and meta["stylesheet_links"] > 5:
        add_issue(
            issues, "many-stylesheets", "low", "performance",
            "Many render-blocking stylesheet links in the document head.",
            rel, 0, {"count": meta["stylesheet_links"]},
            "Bundle critical CSS, defer non-critical CSS and check whether every stylesheet is needed on first paint.",
            "confirmed",
        )
    if is_global and meta["blocking_scripts"]:
        add_issue(
            issues, "blocking-scripts", "low", "performance",
            "External scripts without defer/async/module in the document.",
            rel, 0, {"scripts": meta["blocking_scripts"][:10]},
            "Load non-critical scripts with defer, async or type=module; remove scripts that are not needed on first paint.",
            "confirmed",
        )


def validate_hreflang(value: str) -> bool:
    if value == "x-default":
        return True
    if not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z]{2}|-[A-Za-z]{4})?", value):
        return False
    parts = value.split("-")
    if len(parts) == 1:
        return True
    return parts[0].lower() not in ("uk", "eu", "un") and parts[1].upper() not in ("UK", "EU", "UN")


def analyze_keywords(
    keyword_data: Any,
    routes: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    if not keyword_data:
        return {"provided": False, "mapped": 0, "covered": 0}
    entries: list[dict[str, Any]] = []
    if isinstance(keyword_data, dict) and "pages" in keyword_data:
        entries = [item for item in keyword_data["pages"] if isinstance(item, dict)]
    elif isinstance(keyword_data, dict):
        for url, value in keyword_data.items():
            if isinstance(value, dict):
                entries.append({"url": url, **value})
            elif isinstance(value, str):
                entries.append({"url": url, "primary": value})
    elif isinstance(keyword_data, list):
        entries = [item for item in keyword_data if isinstance(item, dict)]

    route_by_url = {route["route"]: route for route in routes}
    primary_owner: dict[str, list[str]] = {}
    covered = 0
    for entry in entries:
        url = str(entry.get("url") or entry.get("route") or "").strip()
        primary = str(entry.get("primary") or entry.get("keyword") or "").strip()
        if not url or not primary:
            continue
        route = route_by_url.get(url) or route_by_url.get(url.rstrip("/")) or route_by_url.get("/" + url.lstrip("/"))
        if route and route.get("private"):
            continue
        if not route:
            add_issue(
                issues, "keyword-route-not-found", "low", "keywords",
                f"Keyword map points at {url!r}, but no route was detected.",
                "", 0, {"url": url, "primary": primary},
                "Check the route path or add the missing route to the map.",
                "likely",
            )
            continue
        primary_owner.setdefault(primary.lower(), []).append(url)
        haystacks = {
            "title": route["title"],
            "h1": route["h1"],
            "description": route["description"],
        }
        missing = [field for field, value in haystacks.items() if value and primary.lower() not in value.lower()]
        if not any(haystacks.values()):
            add_issue(
                issues, "keyword-target-no-metadata", "medium", "keywords",
                f"Target keyword {primary!r} is mapped, but the route has no title/H1 to carry it.",
                route["file"], 0, {"route": url, "primary": primary},
                "Add page-specific metadata and an H1 that express the target intent.",
                "likely",
            )
        elif missing:
            add_issue(
                issues, "keyword-missing-in-field", "medium", "keywords",
                f"Target keyword {primary!r} is missing from: {', '.join(missing)}.",
                route["file"], 0, {"route": url, "primary": primary, "missing": missing},
                "Use the target phrase naturally in the title, H1 and opening section; do not stuff it.",
                "likely",
            )
        else:
            covered += 1
        title = route["title"]
        if title and title.lower().count(primary.lower()) > 2:
            add_issue(
                issues, "keyword-stuffing", "low", "keywords",
                f"Target keyword appears {title.lower().count(primary.lower())} times in the title.",
                route["file"], 0, {"primary": primary, "title": title},
                "Write for people; avoid repeating the same phrase in the title.",
                "confirmed",
            )
    for primary, urls in primary_owner.items():
        if len(urls) > 1:
            add_issue(
                issues, "keyword-cannibalization", "high", "keywords",
                f"Target keyword {primary!r} is mapped to {len(urls)} URLs.",
                "", 0, {"primary": primary, "urls": urls},
                "Choose one owner URL per intent; merge, redirect or re-target the others.",
                "likely",
            )
    return {"provided": True, "mapped": len(entries), "covered": covered}


def compute_score(issues: list[dict[str, Any]]) -> int:
    per_rule: dict[str, int] = {}
    for issue in issues:
        per_rule[issue["rule"]] = per_rule.get(issue["rule"], 0) + SEVERITY_WEIGHT.get(issue["severity"], 1)
    return max(0, 100 - sum(min(value, 20) for value in per_rule.values()))


def group_issues(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for issue in issues:
        item = grouped.setdefault(
            issue["rule"],
            {
                "rule": issue["rule"],
                "severity": issue["severity"],
                "category": issue["category"],
                "message": issue["message"],
                "fix": issue["fix"],
                "confidence": issue["confidence"],
                "count": 0,
                "locations": [],
            },
        )
        item["count"] += 1
        location = f"{issue['file']}:{issue['line']}" if issue["file"] else issue.get("evidence", {}).get("route", "")
        if location and location not in item["locations"]:
            item["locations"].append(location)
        if SEVERITY_WEIGHT.get(issue["severity"], 1) > SEVERITY_WEIGHT.get(item["severity"], 1):
            item["severity"] = issue["severity"]
            item["message"] = issue["message"]
            item["fix"] = issue["fix"]
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    return sorted(grouped.values(), key=lambda item: (order.get(item["severity"], 5), -item["count"], item["rule"]))


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    project = report["project"]
    score = summary.get("score")
    score_line = (
        f"- Score (triage only): **{score}/100**"
        if score is not None
        else "- Score: **not applicable** (inventory/context scope, not a public site)"
    )
    apps = project.get("apps") or []
    app_lines = [
        f"| `{item.get('path', '')}` | {item.get('kind', '')} | {', '.join(item.get('evidence', [])[:2])} |"
        for item in apps[:20]
    ]
    lines = [
        "# Repository SEO Review",
        "",
        f"**Project:** {project['framework_label']} · {project['rendering_label']} · scope **{project.get('app_type', 'public')}**",
        f"**Root:** `{report['root']}`",
        f"**Generated:** {report['generated_at']}",
        "",
        "## Verdict",
        "",
        report["verdict"],
        "",
        *([f"> **Scope warning:** {summary['scope_warning']}", ""] if summary.get("scope_warning") else []),
        score_line,
        f"- Findings: **{summary['issue_count']}** "
        f"({', '.join(f'{key}: {value}' for key, value in summary['issues_by_severity'].items()) or 'none'})",
        f"- Files scanned: **{summary['files_scanned']}** · routes detected: **{summary['routes_detected']}**",
        f"- Rendering risk: **{project['rendering_risk']}**",
        "",
    ]
    if apps:
        lines += [
            "## Apps / services in this repository",
            "",
            "| Path | Kind | Evidence |",
            "|---|---|---|",
            *app_lines,
            "",
        ]
    if project.get("context_sources"):
        lines += [
            "## Context sources (not web routes)",
            "",
            *[f"- `{item}`" for item in project["context_sources"]],
            "",
        ]
    lines += [
        "## Top findings",
        "",
    ]
    for item in report["top_issues"][:20]:
        lines += [
            f"### {item['severity'].upper()} · `{item['rule']}` ({item['count']}×)",
            "",
            item["message"],
            "",
            f"- Evidence: {', '.join(item['locations'][:8]) or 'see report.json'}",
            f"- Fix: {item['fix']}",
            f"- Confidence: {item['confidence']}",
            "",
        ]
    lines += [
        "## Route inventory",
        "",
        "| Route | File | Title | H1 | Description | JSON-LD |",
        "|---|---|---|---|---|---|",
    ]
    for route in report["routes"][:100]:
        lines.append(
            f"| `{route['route']}` | `{route['file']}` | {'yes' if route['title'] else '**no**'} | "
            f"{route['h1_count']} | {'yes' if route['description'] else 'no'} | {route['jsonld_types'] or '—'} |"
        )
    if len(report["routes"]) > 100:
        lines.append(f"| … | {len(report['routes']) - 100} more routes | | | | |")
    lines += [
        "",
        "## Method and limits",
        "",
        "- Static source scan only; no JavaScript execution, no browser render, no live HTTP evidence.",
        "- Framework detection and route extraction are heuristics; verify each finding in the code.",
        "- A finding marked `likely` or `hypothesis` is a lead, not a confirmed defect.",
        "- The score is triage, not a ranking prediction. No traffic, CTR or revenue is inferred.",
        "",
    ]
    if report.get("keyword_coverage"):
        coverage = report["keyword_coverage"]
        lines += [
            "## Keyword coverage",
            "",
            f"- Keyword map provided: {coverage.get('provided')}",
            f"- Mapped targets: {coverage.get('mapped')} · fully covered: {coverage.get('covered')}",
            "",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_issues_csv(report: dict[str, Any], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["severity", "rule", "category", "confidence", "file", "line", "message"])
        for issue in report["issues"]:
            writer.writerow([
                issue["severity"], issue["rule"], issue["category"], issue["confidence"],
                issue["file"], issue["line"], issue["message"],
            ])


def write_routes_csv(report: dict[str, Any], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "route", "file", "title", "description", "canonical",
            "h1_count", "jsonld_types", "noindex", "private",
        ])
        for route in report["routes"]:
            writer.writerow([
                route["route"], route["file"], route["title"], route["description"],
                route["canonical"], route["h1_count"], route["jsonld_types"],
                route["noindex"], route.get("private", False),
            ])


def finalize_report(
    *,
    root: Path,
    framework: str,
    rendering: str,
    rendering_risk: str,
    rendering_notes: list[str],
    prerender_detected: bool,
    package_files: list[str],
    files: list[Path],
    skipped: int,
    routes: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    app_type: str,
    scope_note: str,
    apps: list[dict[str, Any]],
    context: list[str],
    build: dict[str, Any],
    keyword_coverage: dict[str, Any],
    score_applicable: bool,
) -> dict[str, Any]:
    summary_counts: dict[str, int] = {}
    confidence_counts: dict[str, int] = {}
    for issue in issues:
        summary_counts[issue["severity"]] = summary_counts.get(issue["severity"], 0) + 1
        confidence_counts[issue["confidence"]] = confidence_counts.get(issue["confidence"], 0) + 1
    score = compute_score(issues) if score_applicable else None
    verdict = (
        (
            f"SCOPE: {app_type}. {scope_note} "
            f"{len(issues)} scope findings, no site score. "
            "Scan each public app root and each public domain separately."
        )
        if not score_applicable
        else (
            (f"SCOPE WARNING: {scope_note} " if scope_note else "")
            + f"{FRAMEWORK_LABELS.get(framework, framework)} detected. "
            f"{RENDERING_LABELS.get(rendering, rendering)} with {rendering_risk} rendering risk. "
            f"{len(issues)} findings, {len(routes)} routes. "
            "Review the findings before changing code; this is a source scan, not a live index check."
        )
    )
    return {
        "tool": {"name": TOOL_NAME, "version": VERSION},
        "root": str(root),
        "generated_at": now_iso(),
        "project": {
            "framework": framework,
            "framework_label": FRAMEWORK_LABELS.get(framework, framework),
            "rendering": rendering,
            "rendering_label": RENDERING_LABELS.get(rendering, rendering),
            "rendering_risk": rendering_risk,
            "rendering_notes": rendering_notes,
            "prerender_detected": prerender_detected,
            "package_files": package_files,
            "app_type": app_type,
            "score_applicable": score_applicable,
            "apps": apps,
            "context_sources": context,
            "build_context": {
                key: value for key, value in build.items()
                if key != "evidence"
            },
            "build_evidence": build.get("evidence", [])[:10],
        },
        "summary": {
            "score": score,
            "score_applicable": score_applicable,
            "files_scanned": len(files),
            "files_skipped": skipped,
            "routes_detected": len(routes),
            "issue_count": len(issues),
            "issues_by_severity": summary_counts,
            "issues_by_confidence": confidence_counts,
            "scope_warning": scope_note,
        },
        "verdict": verdict,
        "keyword_coverage": keyword_coverage,
        "routes": routes,
        "top_issues": group_issues(issues),
        "issues": issues,
    }


def scan(
    root: Path,
    max_files: int,
    keyword_data: Any,
    excludes: list[str] | None = None,
    include_dist: bool = False,
    scope: str = "auto",
) -> dict[str, Any]:
    files, skipped = iter_files(root, max_files, excludes, include_dist=include_dist)
    deps, package_files = load_packages(files, root)
    framework = detect_framework(root, files, deps)
    rendering, rendering_risk, rendering_notes = detect_rendering(framework, files, root)
    route_map = build_route_map(files, root)
    build = detect_build_context(root)
    apps = discover_apps(root, files)
    preliminary_routes: set[str] = set()
    for path in files:
        preliminary_routes.update(routes_for_file(path, root, framework, route_map))
    app_type, scope_note = classify_scope(
        root, files, framework, len(preliminary_routes), package_files, build, scope
    )
    context = context_sources(root) if app_type in ("umbrella", "docs") else []
    if app_type in ("umbrella", "docs", "local-tool", "backend", "internal", "context"):
        issues: list[dict[str, Any]] = []
        inventory_routes: list[dict[str, Any]] = []
        if app_type == "internal":
            seen_inventory: set[tuple[str, str]] = set()
            for path in files:
                rel = relpath(path, root)
                for route in routes_for_file(path, root, framework, route_map):
                    key = (route, rel)
                    if key in seen_inventory:
                        continue
                    seen_inventory.add(key)
                    inventory_routes.append({
                        "route": route,
                        "file": rel,
                        "title": "",
                        "description": "",
                        "canonical": "",
                        "h1_count": 0,
                        "h1": "",
                        "has_metadata_api": False,
                        "has_jsonld": False,
                        "jsonld_types": "",
                        "images": 0,
                        "noindex": True,
                        "private": True,
                    })
        if app_type == "umbrella":
            label = ", ".join(item["path"] for item in apps[:12]) or "see submodules"
            scope_note = f"{scope_note} App roots: {label}."
            add_issue(
                issues, "scan-scope", "info", "measurement", scope_note,
                "", 0, {"apps": apps, "submodules": parse_gitmodules(root)},
                "Run the scanner once per app root and once per public domain; do not score the umbrella root.",
                "confirmed",
            )
        elif app_type == "internal":
            add_issue(
                issues, "internal-not-scored", "info", "measurement", scope_note,
                "", 0, {"index_html": (root / "index.html").exists()},
                "Only check for accidental indexability; do not apply marketing SEO scoring.",
                "confirmed",
            )
        elif app_type == "backend":
            add_issue(
                issues, "backend-not-scored", "info", "measurement", scope_note,
                "", 0, {"build": build},
                "Pair the service with its frontend app; audit public HTML/live URLs, not the API service.",
                "confirmed",
            )
        else:
            add_issue(
                issues, "not-an-app", "info", "measurement", scope_note,
                "", 0, {"context_sources": context, "apps": apps},
                "Use the repository as context (keywords/strategy), not as a web route inventory.",
                "confirmed",
            )
        return finalize_report(
            root=root,
            framework=framework,
            rendering=rendering,
            rendering_risk=rendering_risk,
            rendering_notes=rendering_notes,
            prerender_detected=bool(build.get("prerender")),
            package_files=package_files,
            files=files,
            skipped=skipped,
            routes=inventory_routes,
            issues=issues,
            app_type=app_type,
            scope_note=scope_note,
            apps=apps,
            context=context,
            build=build,
            keyword_coverage=analyze_keywords(keyword_data, [], issues),
            score_applicable=False,
        )

    issues: list[dict[str, Any]] = []
    routes: list[dict[str, Any]] = []
    seen_route_files: set[str] = set()
    seen_routes: set[str] = set()
    mapped_routes = {route for variants in route_map.values() for route in variants}
    hreflang_all: list[dict[str, Any]] = []
    has_sitemap = bool(build.get("sitemap"))
    has_404 = bool(build.get("not_found"))
    has_robots = bool(build.get("robots"))
    has_redirects = False
    spa_fallback = False
    i18n = False
    prerender_detected = bool(build.get("prerender")) or any("prerender" in path.name.lower() for path in files)
    catchall_redirect = False
    locales = {
        match.group(1).lower()
        for rel in (relpath(path, root) for path in files)
        if re.search(r"/(?:locales?|translations?|i18n)/", rel, re.I)
        for match in [re.search(r"/([a-z]{2}(?:[-_][a-z]{2})?)\.(?:json|ts|js|ya?ml)$", rel, re.I)]
        if match
    }
    i18n = len(locales) >= 2
    route_locales = {
        match.group(1).lower()
        for variants in route_map.values()
        for route in variants
        for match in [re.match(r"/([a-z]{2})(?:/|$)", route, re.I)]
        if match
    }
    i18n = i18n or len(route_locales) >= 2
    static_export = any(
        re.search(r"output\s*:\s*['\"]export['\"]", read_text(path))
        for path in files
        if path.name.startswith("next.config.")
    )
    layout_defaults = False
    if framework == "next-app":
        for path in files:
            rel = relpath(path, root)
            if is_root_layout_file(rel, path.name.lower(), framework):
                layout_defaults = bool(re.search(r"\b(?:title|description)\s*:", read_text(path)))
                break

    for path in files:
        rel = relpath(path, root)
        text = read_text(path)
        lower = text.lower()
        name = path.name.lower()

        if name == "robots.txt":
            has_robots = True
            if re.search(r"(?im)^\s*disallow:\s*/\s*$", text) and not re.search(r"(?im)^\s*allow:\s*/\s*$", text):
                add_issue(
                    issues, "robots-blocks-all", "critical", "indexing",
                    "robots.txt disallows the whole site.",
                    rel, line_of(text, re.search(r"(?im)^\s*disallow:\s*/\s*$", text) or 0),
                    {"robots": text[:500]},
                    "Allow public pages; use noindex for individual pages that must stay out of search.",
                    "confirmed",
                )
            if re.search(r"(?im)^\s*disallow:\s*/(?:_next|static|assets)/", text):
                add_issue(
                    issues, "robots-blocks-assets", "high", "indexing",
                    "robots.txt blocks CSS/JS asset paths that Google needs to render pages.",
                    rel, 0, {"robots": text[:500]},
                    "Allow the asset paths required for rendering; block only crawl waste.",
                    "confirmed",
                )
            if not re.search(r"(?im)^\s*sitemap:\s*https?://", text):
                add_issue(
                    issues, "robots-no-sitemap", "low", "indexing",
                    "robots.txt has no absolute Sitemap line.",
                    rel, 0, {},
                    "Add Sitemap: https://example.com/sitemap.xml.",
                    "confirmed",
                )

        if name in ("robots.ts", "robots.js", "robots.mjs", "robots.tsx"):
            has_robots = True

        if name.startswith("sitemap") or "next-sitemap" in lower or "@astrojs/sitemap" in lower or "@nuxtjs/sitemap" in lower or "django.contrib.sitemaps" in lower:
            has_sitemap = True
        if name in ("404.html", "404.htm", "404.astro", "not-found.tsx", "not-found.jsx", "not-found.js", "not-found.vue", "error.vue", "+error.svelte"):
            has_404 = True
        if re.search(r"\[\[?\.\.\.", rel):
            has_404 = True
        if name in ("vercel.json", "netlify.toml", "nginx.conf", "web.config", ".htaccess") and re.search(r"rewrite|redirect|try_files|proxy_pass", lower):
            has_redirects = True
        if name in ("next.config.js", "next.config.mjs", "next.config.ts"):
            if re.search(r"rewrites\s*\([^)]*\)[\s\S]{0,500}(index\.html|/:path\*)", text):
                spa_fallback = True
            if re.search(r"redirects\s*\(", text):
                has_redirects = True
        if name in ("vercel.json", "netlify.toml", "nginx.conf", "web.config", ".htaccess") and re.search(r"(index\.html|try_files[^\n]*/index\.html)", lower):
            spa_fallback = True
        if re.search(r"\bhreflang\b", lower):
            for match in re.finditer(r"hreflang\s*[:=]\s*['\"]([^'\"]+)['\"]", text, re.I):
                value = match.group(1)
                if any(marker in value for marker in ("${", "{", "}", "%", "' +", '" +')):
                    continue
                hreflang_all.append({"value": value, "file": rel, "line": line_of(text, match)})
        if re.search(r"<Route\b[^>]*\bpath\s*=\s*['\"]\*['\"]", text) and re.search(r"\bNavigate\b", text):
            catchall_redirect = True

        if framework in ("vite-spa", "static") and name == "index.html":
            if re.search(r"<div\s+id=['\"](root|app)['\"]\s*>\s*</div>", text, re.I) or re.search(r"<app-root", text, re.I):
                build_external = prerender_detected or (
                    bool(build.get("built_html")) and root.name.lower() not in ("dist", "build", "out")
                )
                add_issue(
                    issues, "csr-only-shell", "info" if build_external else "high", "rendering",
                    (
                        "index.html is a client-rendered shell; a prerender/build step exists outside this root, "
                        "so verify the built per-route HTML before treating this as a defect."
                        if build_external
                        else "index.html contains an empty app shell; public content is client-rendered."
                    ),
                    rel, 0, {"file": rel, "prerender_detected": build_external},
                    "Verify the built HTML. If prerendering is configured, confirm each public route ships title, H1 and links in the HTML; otherwise add SSR/prerender.",
                    "likely" if build_external else "confirmed",
                )
        if framework == "angular" and name == "index.html" and "<app-root" in lower:
            add_issue(
                issues, "csr-only-shell", "high", "rendering",
                "Angular index.html ships an empty <app-root> shell.",
                rel, 0, {"file": rel},
                "Use Angular SSR/prerendering for public pages; keep the SPA for authenticated areas.",
                "confirmed",
            )

        variants = routes_for_file(path, root, framework, route_map)
        if is_email_template(rel):
            variants = []
        if framework == "vite-spa" and path.suffix.lower() in (".html", ".htm"):
            # A React Router source page with the same path is better evidence
            # than the Vite HTML shell (which only carries the generic head).
            variants = [variant for variant in variants if variant not in mapped_routes]
        if variants:
            variants.sort(key=lambda value: (0 if value.startswith("/de/") or value == "/" else 1, value))
            route = variants[0]
            seen_route_files.add(rel)
            analyze_route(
                path, root, rel, route, text, framework, issues, routes,
                private_route=is_private_route(route),
                layout_defaults=layout_defaults,
                static_export=static_export,
            )
            if routes:
                base_entry = routes[-1]
                for variant in variants[1:]:
                    entry = dict(base_entry)
                    entry["route"] = variant
                    entry["derived"] = True
                    routes.append(entry)
        elif is_layout_file(path, framework) or name in ("_app.tsx", "_app.jsx", "_document.tsx", "_document.jsx", "root.tsx", "layout.tsx", "layout.jsx", "app.vue", "+layout.svelte"):
            analyze_global_file(
                path, rel, text, framework, issues,
                is_global=is_root_layout_file(rel, name, framework),
            )

        if path.suffix.lower() in (".css", ".scss", ".sass", ".less") and "@import" in lower:
            bundled = framework in (
                "next-app", "next-pages", "nuxt", "sveltekit", "astro",
                "remix", "vite-spa", "angular",
            )
            add_issue(
                issues, "css-import", "info" if bundled else "low", "performance",
                "CSS uses @import."
                + (" The bundler normally inlines it at build time; verify the built CSS." if bundled else ""),
                rel, 0, {"framework": framework},
                "Bundle imports at build time or use a preload for critical CSS.",
                "likely" if bundled else "confirmed",
            )

    if framework == "vite-spa":
        add_issue(
            issues, "csr-only-app", "info" if prerender_detected else "high", "rendering",
            (
                "The SPA has a prerender/build step outside this root; verify the built HTML instead of treating CSR as a defect."
                if prerender_detected
                else "The project is a client-side SPA; no SSR/SSG layer was detected in this root."
            ),
            "package.json" if (root / "package.json").exists() else "vite.config", 0,
            {"framework": framework, "prerender_detected": prerender_detected},
            "If a prerender step exists, verify the built HTML for each public route. Otherwise add SSR/SSG or a prerender step for public content; keep CSR for app screens.",
            "likely" if prerender_detected else "confirmed",
        )
    if framework == "angular":
        add_issue(
            issues, "csr-only-app", "high", "rendering",
            "The project is an Angular SPA without an SSR/prerender step.",
            "angular.json", 0, {"framework": framework},
            "Enable Angular SSR/prerendering for public pages.",
            "likely",
        )

    if not has_sitemap:
        add_issue(
            issues, "sitemap-missing", "low", "indexing",
            "No sitemap generator or sitemap file found.",
            "", 0, {"framework": framework},
            "Generate a sitemap from the route/content inventory; link it from robots.txt.",
            "confirmed",
        )
    default_404 = framework in ("next-app", "next-pages", "sveltekit", "nuxt", "remix")
    if not has_404 and not default_404:
        if catchall_redirect:
            add_issue(
                issues, "soft-404-redirect", "medium", "indexing",
                "Unknown routes are redirected to the home page instead of returning a real 404.",
                "", 0, {"framework": framework},
                "Add a real 404 route and a server-side 404 status; do not send 200 for unknown paths.",
                "confirmed",
            )
        else:
            add_issue(
                issues, "not-found-missing", "medium", "indexing",
                "No dedicated 404/error route found.",
                "", 0, {"framework": framework},
                "Add a real 404 route that returns HTTP 404; do not serve a 200 page that says \"not found\".",
                "likely",
            )
    if not has_robots:
        add_issue(
            issues, "robots-missing", "low", "indexing",
            "No robots.txt found.",
            "", 0, {"framework": framework},
            "Add robots.txt with crawl rules and an absolute sitemap URL.",
            "confirmed",
        )
    if spa_fallback:
        add_issue(
            issues, "spa-fallback", "high", "indexing",
            "The server rewrites unknown paths to index.html.",
            "", 0, {},
            "Return a real 404 for unknown paths; a catch-all SPA fallback creates soft 404s.",
            "likely",
        )
    if i18n and not hreflang_all:
        if build.get("hreflang_in_sitemap"):
            add_issue(
                issues, "hreflang-missing-in-html", "low", "internationalization",
                "hreflang is only declared in the sitemap, not in the HTML head.",
                "", 0, {"sitemap_hreflang": True},
                "Keep the sitemap alternates and add reciprocal HTML <link rel=alternate hreflang> tags for non-Google crawlers and consistency.",
                "confirmed",
            )
        else:
            add_issue(
                issues, "hreflang-missing", "medium", "internationalization",
                "Internationalization is configured, but no hreflang annotations were found in HTML or the sitemap.",
                "", 0, {},
                "Add reciprocal hreflang links (including self-reference) for each locale, or document why the site is single-language.",
                "likely",
            )
    for item in hreflang_all:
        if not validate_hreflang(item["value"]):
            add_issue(
                issues, "hreflang-invalid", "medium", "internationalization",
                f"Invalid hreflang value: {item['value']!r}.",
                item["file"], item["line"], {"hreflang": item["value"]},
                "Use ISO 639-1 language plus optional ISO 3166-1 Alpha 2 region, or x-default.",
                "confirmed",
            )

    titles: dict[str, list[str]] = {}
    descriptions: dict[str, list[str]] = {}
    for route in routes:
        if route.get("private") or route.get("derived"):
            continue
        if route["title"]:
            titles.setdefault(route["title"].lower(), []).append(route["route"])
        if route["description"]:
            descriptions.setdefault(route["description"].lower(), []).append(route["route"])
    for title, urls in titles.items():
        if len(urls) > 1:
            add_issue(
                issues, "title-duplicate", "high", "on-page",
                "Multiple routes share the same title.",
                "", 0, {"title": title, "routes": urls},
                "Give each route a unique title that describes its specific intent.",
                "confirmed",
            )
    for description, urls in descriptions.items():
        if len(urls) > 1:
            add_issue(
                issues, "description-duplicate", "medium", "on-page",
                "Multiple routes share the same meta description.",
                "", 0, {"description": description, "routes": urls},
                "Write a page-specific description for each route.",
                "confirmed",
            )

    keyword_coverage = analyze_keywords(keyword_data, routes, issues)

    scope_warning = scope_note
    if not routes and not build.get("built_html") and not build.get("route_registry"):
        scope_warning = (
            scope_note
            or "A web framework or package was detected but no routes were found at this root. "
               "Verify the scan root (monorepo app folder?) before using this report."
        )
    if scope_warning:
        add_issue(
            issues, "scan-scope", "info", "measurement", scope_warning,
            "", 0, {"package_files": package_files[:10], "framework": framework, "apps": apps},
            "Run the scanner on the app root; do not treat this report as a site audit.",
            "confirmed",
        )

    return finalize_report(
        root=root,
        framework=framework,
        rendering=rendering,
        rendering_risk=rendering_risk,
        rendering_notes=rendering_notes,
        prerender_detected=prerender_detected,
        package_files=package_files,
        files=files,
        skipped=skipped,
        routes=routes,
        issues=issues,
        app_type=app_type,
        scope_note=scope_warning,
        apps=apps,
        context=context,
        build=build,
        keyword_coverage=keyword_coverage,
        score_applicable=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evidence-based repository SEO scanner")
    parser.add_argument("root", nargs="?", default=".", help="Repository root")
    parser.add_argument("--out", default="seo-repo-report")
    parser.add_argument("--max-files", type=int, default=3000)
    parser.add_argument("--keywords", help="Optional JSON keyword map (route -> primary/secondary)")
    parser.add_argument("--exclude", action="append", default=[], help="Glob to exclude, repeatable (e.g. 'src/generated/*')")
    parser.add_argument("--include-dist", action="store_true", help="Scan built dist/build/out HTML too (default: source only)")
    parser.add_argument(
        "--scope", choices=("auto", "public", "internal", "context"), default="auto",
        help="Force app scope; auto classifies umbrella/docs/local/backend/internal apps and does not score them",
    )
    parser.add_argument("--format", choices=("json", "md", "both"), default="both")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    keyword_data = None
    if args.keywords:
        try:
            keyword_data = json.loads(Path(args.keywords).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"cannot read keyword map: {exc}", file=sys.stderr)
            return 2

    report = scan(
        root,
        max(1, args.max_files),
        keyword_data,
        args.exclude,
        include_dist=args.include_dist,
        scope=args.scope,
    )
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.format in ("json", "both"):
        (out_dir / "repo-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    if args.format in ("md", "both"):
        write_markdown(report, out_dir / "repo-report.md")
        write_issues_csv(report, out_dir / "issues.csv")
        write_routes_csv(report, out_dir / "routes.csv")
    score = report["summary"]["score"]
    score_label = f"{score}/100" if score is not None else "not scored"
    print(
        f"{report['project']['framework_label']} · {report['project']['rendering_label']} · "
        f"score {score_label} · {report['summary']['issue_count']} issues · "
        f"{report['summary']['routes_detected']} routes · scope {report['project']['app_type']}"
    )

    print(f"Report: {out_dir / 'repo-report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
