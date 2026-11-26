#!/usr/bin/env python3
"""Evidence-based static SEO scanner (v0.2).

No third-party dependencies. Crawls a site, collects evidence and writes
report.json, report.md and pages.csv. The script is deliberately conservative:
it respects robots.txt, follows only same-site links, caps pages and never
claims to know how Google indexes a page.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import deque
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

VERSION = "0.2.4"
TOOL_NAME = "seo-audit"
DEFAULT_UA = "seo-audit/0.3.1 (+https://github.com/johannes3502/seo-audit)"
MAX_BYTES = 2 * 1024 * 1024
SEVERITY_WEIGHT = {"critical": 10, "high": 5, "medium": 2, "low": 1, "info": 0}
AI_BOTS = ("GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended")
LEGAL_NOINDEX = re.compile(
    r"/(?:agb|avv|datenschutz|datenschutzerklaerung|impressum|imprint|privacy|privacy-policy|terms|terms-of-service|legal|legal-notice|cookies?|widerruf|nutzungsbedingungen)(?:/|$)",
    re.I,
)
APP_PATH = re.compile(
    r"/(?:login|signin|sign-in|services|reset-password|forgot-password|404|dashboard|admin|setup|claim|confirm|verify-email|cancel|start|abrechnung|qr)(?:/|$)",
    re.I,
)
DRAFT_MARKERS = re.compile(
    r"(\bseite\s+in\s+arbeit\b|\bin\s+arbeit\b|\bcoming\s+soon\b|"
    r"\bwork\s+in\s+progress\b|\bplatzhalter\b|\bunter\s+konstruktion\b|"
    r"\bseite\s+im\s+aufbau\b|\btodo\s*:|\bdraft\s+(?:version|page)\b|"
    r"\bunver[oö]ffentlicht\b)",
    re.I,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_url(url: str, base: str | None = None) -> str:
    if base:
        url = urllib.parse.urljoin(base, url)
    parts = urllib.parse.urlsplit(url.strip())
    scheme = (parts.scheme or "https").lower()
    host = (parts.hostname or "").lower()
    port = parts.port
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"
    else:
        netloc = host
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    return urllib.parse.urlunsplit((scheme, netloc, path, parts.query, ""))


def url_key(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = parts.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    query = f"?{parts.query}" if parts.query else ""
    return f"{parts.scheme.lower()}://{host}{path}{query}"


def host_key(url: str) -> str:
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def netloc_key(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower()
    try:
        port = parts.port
    except ValueError:
        port = None
    if port and not ((parts.scheme.lower() == "http" and port == 80) or (parts.scheme.lower() == "https" and port == 443)):
        return f"{host}:{port}"
    return host


def same_site(url: str, start_url: str) -> bool:
    return host_key(url) == host_key(start_url)


SKIP_PATTERNS = (
    "/cart",
    "/checkout",
    "/warenkorb",
    "/kasse",
    "/account",
    "/mein-konto",
    "/wp-admin",
    "/wp-login",
    "/logout",
    "add-to-cart",
    "?s=",
    "/search?",
)


def should_skip(url: str) -> bool:
    parts = urllib.parse.urlsplit(url)
    haystack = (parts.path + "?" + parts.query).lower()
    return any(pattern in haystack for pattern in SKIP_PATTERNS)


def valid_hreflang(value: str) -> bool:
    if value == "x-default":
        return True
    if not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z]{2}|-[A-Za-z]{4})?", value):
        return False
    parts = value.split("-")
    if len(parts) == 1:
        return True
    return parts[0].lower() not in ("uk", "eu", "un") and parts[1].upper() not in ("UK", "EU", "UN")


def header(headers: dict[str, str], name: str) -> str:
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return ""


def decode_body(body: bytes, headers: dict[str, str]) -> str:
    content_type = header(headers, "content-type")
    match = re.search(r"charset=([\w-]+)", content_type, re.I)
    encoding = match.group(1) if match else "utf-8"
    try:
        return body.decode(encoding, errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


def is_html(headers: dict[str, str]) -> bool:
    content_type = header(headers, "content-type").lower()
    return "text/html" in content_type or "application/xhtml+xml" in content_type


def clean_text(value: str) -> str:
    return " ".join((value or "").split())


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def ssl_context(insecure: bool = False) -> ssl.SSLContext:
    if insecure:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
    try:
        import certifi  # optional: fixes missing system CAs on some Windows setups

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        context = ssl.create_default_context()
        try:
            context.load_default_certs()
        except Exception:
            pass
        return context


def fetch(
    url: str,
    timeout: float,
    user_agent: str,
    max_bytes: int = MAX_BYTES,
    insecure: bool = False,
) -> dict[str, Any]:
    started = time.perf_counter()
    current = url
    chain: list[dict[str, Any]] = []
    headers: dict[str, str] = {}
    body = b""
    status: int | None = None
    error: str | None = None

    for _ in range(6):
        request = urllib.request.Request(
            current,
            headers={
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip",
                "Connection": "close",
            },
        )
        opener = urllib.request.build_opener(
            _NoRedirect(),
            urllib.request.HTTPSHandler(context=ssl_context(insecure)),
        )
        try:
            response = opener.open(request, timeout=timeout)
            status = getattr(response, "status", None) or response.getcode()
            headers = dict(response.headers.items())
            body = response.read(max_bytes + 1)
        except urllib.error.HTTPError as exc:
            status = exc.code
            headers = dict(exc.headers.items()) if exc.headers else {}
            try:
                body = exc.read(max_bytes + 1)
            except Exception:
                body = b""
        except Exception as exc:  # noqa: BLE001 - network failures are evidence too
            error = f"{type(exc).__name__}: {exc}"
            break

        if status in (301, 302, 303, 307, 308):
            location = header(headers, "location")
            chain.append({"url": current, "status": status, "location": location})
            if not location:
                break
            current = normalize_url(urllib.parse.urljoin(current, location))
            continue
        break

    if header(headers, "content-encoding").lower() == "gzip" and body:
        try:
            body = gzip.decompress(body)
        except OSError:
            pass
    truncated = len(body) > max_bytes
    body = body[:max_bytes]
    return {
        "requested_url": url,
        "final_url": current,
        "status": status,
        "headers": headers,
        "body": body,
        "chain": chain,
        "error": error,
        "truncated": truncated,
        "response_time_ms": int((time.perf_counter() - started) * 1000),
    }


class Robots:
    def __init__(self, text: str):
        self.text = text or ""
        self.sitemaps: list[str] = []
        self.groups: list[dict[str, Any]] = []
        self._parse()

    def _parse(self) -> None:
        current: dict[str, Any] | None = None
        for raw in self.text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if key == "user-agent":
                if current is None or current["rules"]:
                    current = {"agents": [], "rules": [], "crawl_delay": None}
                    self.groups.append(current)
                current["agents"].append(value.lower())
            elif key == "sitemap":
                self.sitemaps.append(value)
            elif current is not None and key in ("allow", "disallow"):
                current["rules"].append((key == "allow", value))
            elif current is not None and key == "crawl-delay":
                try:
                    current["crawl_delay"] = float(value)
                except ValueError:
                    pass

    def _rules_for(self, agent: str) -> list[tuple[bool, str]]:
        needle = agent.lower()
        rules: list[tuple[bool, str]] = []
        for group in self.groups:
            if any(a == "*" or a in needle or needle in a for a in group["agents"]):
                rules.extend(group["rules"])
        return rules

    @staticmethod
    def _matches(pattern: str, path: str) -> bool:
        if not pattern:
            return False
        anchored = pattern.endswith("$")
        pattern = pattern[:-1] if anchored else pattern
        regex = "^" + re.escape(pattern).replace(r"\*", ".*") + ("$" if anchored else "")
        return re.match(regex, path) is not None

    def is_allowed(self, url: str, agent: str) -> bool:
        parts = urllib.parse.urlsplit(url)
        path = parts.path or "/"
        if parts.query:
            path += "?" + parts.query
        best: tuple[int, bool] | None = None
        for allow, pattern in self._rules_for(agent):
            if self._matches(pattern, path):
                score = len(pattern)
                if best is None or score > best[0] or (score == best[0] and allow):
                    best = (score, allow)
        return True if best is None else best[1]

    def crawl_delay(self, agent: str) -> float:
        needle = agent.lower()
        for group in self.groups:
            if any(a == "*" or a in needle or needle in a for a in group["agents"]):
                if group["crawl_delay"]:
                    return float(group["crawl_delay"])
        return 0.0


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.in_title = False
        self.metas: list[dict[str, str]] = []
        self.links: list[dict[str, str]] = []
        self.hreflang: list[dict[str, str]] = []
        self.scripts: list[dict[str, str]] = []
        self.images: list[dict[str, Any]] = []
        self.sources: list[dict[str, str]] = []
        self.anchors: list[dict[str, Any]] = []
        self.iframes: list[dict[str, str]] = []
        self.headings: list[tuple[str, str]] = []
        self.current_heading: str | None = None
        self.heading_parts: list[str] = []
        self.current_anchor: dict[str, str] | None = None
        self.anchor_parts: list[str] = []
        self.style_blocks: list[dict[str, Any]] = []
        self.current_style: dict[str, str] | None = None
        self.style_parts: list[str] = []
        self.lang = ""
        self.has_viewport = False
        self.in_body = False
        self.in_noscript = False
        self.noscript_h1 = 0
        self.root_stack: list[dict[str, Any]] = []
        self.empty_shell = False
        self.picture_depth = 0
        self.has_picture = False
        self.skip_text = 0
        self.text_parts: list[str] = []
        self.jsonld_parts: list[str] = []
        self.jsonld_raw: list[str] = []
        self.in_jsonld = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: (value or "") for key, value in attrs}
        tag = tag.lower()
        if tag == "html":
            self.lang = values.get("lang", "")
        elif tag == "body":
            self.in_body = True
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            self.metas.append(values)
            if values.get("name", "").lower() == "viewport":
                self.has_viewport = True
        elif tag == "link":
            self.links.append(values)
            if values.get("hreflang") and values.get("href"):
                self.hreflang.append(
                    {"hreflang": values.get("hreflang", ""), "href": values.get("href", "")}
                )
        elif tag == "script":
            self.scripts.append(values)
            if values.get("type", "").lower() == "application/ld+json":
                self.in_jsonld = True
                self.jsonld_parts = []
            self.skip_text += 1
        elif tag == "style":
            self.current_style = values
            self.style_parts = []
            self.skip_text += 1
        elif tag == "noscript":
            self.in_noscript = True
            self.skip_text += 1
        elif tag == "template":
            self.skip_text += 1
        elif tag == "picture":
            self.picture_depth += 1
            self.has_picture = True
        elif tag == "source":
            self.sources.append(values)
        elif tag == "img":
            values["_in_picture"] = "1" if self.picture_depth > 0 else ""
            self.images.append(values)
        elif tag == "div":
            self.root_stack.append(
                {"id": values.get("id", "").lower(), "text": 0}
            )
        elif tag == "iframe":
            self.iframes.append(values)
        elif tag == "a":
            if self.current_anchor is None:
                self.current_anchor = values
                self.anchor_parts = []
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if tag == "h1" and self.in_noscript:
                self.noscript_h1 += 1
            self.current_heading = tag
            self.heading_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "body":
            self.in_body = False
        elif tag == "title":
            self.in_title = False
        elif tag == "script":
            if self.in_jsonld:
                self.jsonld_raw.append("".join(self.jsonld_parts).strip())
                self.in_jsonld = False
            self.skip_text = max(0, self.skip_text - 1)
        elif tag == "style":
            if self.current_style is not None:
                text = clean_text("".join(self.style_parts))
                self.style_blocks.append(
                    {"attrs": self.current_style, "text": text, "length": len(text)}
                )
                self.current_style = None
                self.style_parts = []
            self.skip_text = max(0, self.skip_text - 1)
        elif tag == "noscript":
            self.in_noscript = False
            self.skip_text = max(0, self.skip_text - 1)
        elif tag == "template":
            self.skip_text = max(0, self.skip_text - 1)
        elif tag == "picture":
            self.picture_depth = max(0, self.picture_depth - 1)
        elif tag == "div" and self.root_stack:
            mount = self.root_stack.pop()
            if mount["id"] in ("root", "app", "__next", "__nuxt") and mount["text"] == 0:
                self.empty_shell = True
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if self.current_heading == tag:
                self.headings.append((tag, clean_text("".join(self.heading_parts))))
                self.current_heading = None
        elif tag == "a" and self.current_anchor is not None:
            self.anchors.append(
                {"attrs": self.current_anchor, "text": clean_text("".join(self.anchor_parts))}
            )
            self.current_anchor = None
            self.anchor_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.in_jsonld:
            self.jsonld_parts.append(data)
        if self.current_style is not None:
            self.style_parts.append(data)
        if self.current_heading is not None:
            self.heading_parts.append(data)
        if self.current_anchor is not None:
            self.anchor_parts.append(data)
        if self.in_body and self.skip_text == 0:
            self.text_parts.append(data)
        if data.strip():
            for mount in self.root_stack:
                mount["text"] += len(data.strip())


def local_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def collect_sitemaps(
    start_url: str,
    robots: Robots,
    fetch_cached,
    max_urls: int = 1000,
) -> dict[str, Any]:
    parts = urllib.parse.urlsplit(start_url)
    base = f"{parts.scheme}://{parts.netloc}"
    candidates = list(robots.sitemaps) or [base + "/sitemap.xml", base + "/sitemap_index.xml"]
    queue = deque(candidates)
    seen: set[str] = set()
    urls: list[str] = []
    errors: list[str] = []
    while queue and len(urls) < max_urls:
        sitemap_url = queue.popleft()
        key = url_key(sitemap_url)
        if key in seen:
            continue
        seen.add(key)
        result = fetch_cached(sitemap_url)
        if result["status"] is None:
            errors.append(f"{sitemap_url}: {result['error']}")
            continue
        if result["status"] >= 400:
            if result["status"] >= 500:
                errors.append(f"{sitemap_url}: HTTP {result['status']}")
            continue
        if not result["body"]:
            errors.append(f"{sitemap_url}: empty body")
            continue
        try:
            root = ET.fromstring(result["body"])
        except ET.ParseError as exc:
            errors.append(f"{sitemap_url}: invalid XML ({exc})")
            continue
        tag = local_tag(root.tag)
        locations = [node.text.strip() for node in root.iter() if local_tag(node.tag) == "loc" and node.text]
        if tag == "sitemapindex":
            queue.extend(locations)
        elif tag == "urlset":
            for location in locations:
                if location not in urls:
                    urls.append(location)
    return {"urls": urls, "errors": errors, "sitemaps": sorted(seen)}


def parse_jsonld(raw_items: list[str]) -> tuple[list[Any], list[str]]:
    parsed: list[Any] = []
    errors: list[str] = []
    for raw in raw_items:
        if not raw:
            continue
        try:
            parsed.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            errors.append(f"JSON-LD: {exc.msg} at line {exc.lineno}")
    return parsed, errors


def collect_types(value: Any, target: list[str]) -> None:
    if isinstance(value, dict):
        node_type = value.get("@type")
        if isinstance(node_type, str):
            target.append(node_type)
        elif isinstance(node_type, list):
            target.extend(str(item) for item in node_type)
        for child in value.values():
            collect_types(child, target)
    elif isinstance(value, list):
        for child in value:
            collect_types(child, target)


def expired_event_nodes(value: Any, today: datetime | None = None) -> list[dict[str, Any]]:
    """Return Event nodes whose endDate is in the past but status says scheduled."""
    today = today or datetime.now(timezone.utc)
    expired: list[dict[str, Any]] = []

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            node_type = node.get("@type")
            types = [node_type] if isinstance(node_type, str) else node_type if isinstance(node_type, list) else []
            if "Event" in types:
                end_raw = node.get("endDate")
                status = str(node.get("eventStatus") or "")
                if end_raw and (not status or status.endswith("EventScheduled")):
                    try:
                        end = datetime.fromisoformat(str(end_raw).replace("Z", "+00:00"))
                    except ValueError:
                        end = None
                    if end is not None:
                        if end.tzinfo is None:
                            end = end.replace(tzinfo=timezone.utc)
                        if end < today:
                            expired.append({
                                "name": clean_text(str(node.get("name") or "")),
                                "endDate": str(end_raw),
                                "eventStatus": status or "missing",
                            })
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return expired


def meta_content(metas: list[dict[str, str]], key: str) -> str:
    key = key.lower()
    for meta in metas:
        if meta.get("name", "").lower() == key or meta.get("property", "").lower() == key:
            return clean_text(meta.get("content", ""))
    return ""


def extract_faq_questions(value: Any, target: list[str]) -> None:
    if isinstance(value, dict):
        node_type = value.get("@type")
        types = [node_type] if isinstance(node_type, str) else node_type if isinstance(node_type, list) else []
        if "FAQPage" in types:
            entities = value.get("mainEntity") or []
            if isinstance(entities, dict):
                entities = [entities]
            for entity in entities:
                if isinstance(entity, dict):
                    name = clean_text(str(entity.get("name", "")))
                    if name:
                        target.append(name)
        elif "Question" in types:
            name = clean_text(str(value.get("name", "")))
            if name:
                target.append(name)
        for child in value.values():
            extract_faq_questions(child, target)
    elif isinstance(value, list):
        for child in value:
            extract_faq_questions(child, target)


def build_page(
    url: str,
    result: dict[str, Any],
    parser: PageParser | None,
    start_url: str,
) -> dict[str, Any]:
    final_url = result["final_url"] or url
    headers = result["headers"]
    page: dict[str, Any] = {
        "url": url,
        "final_url": final_url,
        "status": result["status"],
        "content_type": header(headers, "content-type"),
        "response_time_ms": result["response_time_ms"],
        "redirect_chain": result["chain"],
        "error": result["error"],
        "title": "",
        "title_length": 0,
        "description": "",
        "description_length": 0,
        "canonical": "",
        "robots_meta": "",
        "x_robots": header(headers, "x-robots-tag"),
        "lang": "",
        "has_viewport": False,
        "h1": [],
        "headings": [],
        "word_count": 0,
        "images": [],
        "images_missing_alt": 0,
        "images_missing_dimensions": 0,
        "internal_links": [],
        "external_links": 0,
        "jsonld_types": [],
        "jsonld_errors": [],
        "og": {},
        "twitter": {},
        "mixed_content": [],
        "security_headers": {},
        "script_count": 0,
        "html_bytes": len(result["body"]),
        "text_sample": "",
        "noindex": False,
        "noscript_h1_count": 0,
        "has_inline_css": False,
        "stylesheet_links": 0,
        "font_preloads": 0,
        "preload_images": 0,
        "google_fonts": [],
        "external_scripts_without_defer": [],
        "has_picture": False,
        "sources_count": 0,
        "cache_control": header(headers, "cache-control"),
        "content_encoding": header(headers, "content-encoding").lower(),
        "jsonld_faq_questions": [],
        "jsonld_faq_mismatches": [],
        "hreflang": [],
        "shell_empty": False,
    }
    if parser is None:
        return page

    page["noscript_h1_count"] = parser.noscript_h1
    page["empty_shell"] = parser.empty_shell
    page["hreflang"] = parser.hreflang
    page["has_inline_css"] = any(
        block["length"] > 500 or "data-seo-inline-css" in block["attrs"]
        for block in parser.style_blocks
    )
    page["stylesheet_links"] = sum(
        1 for link in parser.links
        if "stylesheet" in link.get("rel", "").lower()
        and "preload" not in link.get("rel", "").lower()
    )
    page["font_preloads"] = sum(
        1 for link in parser.links
        if "preload" in link.get("rel", "").lower() and link.get("as", "").lower() == "font"
    )
    page["preload_images"] = sum(
        1 for link in parser.links
        if "preload" in link.get("rel", "").lower() and link.get("as", "").lower() == "image"
    )
    page["google_fonts"] = sorted(
        link["href"] for link in parser.links
        if "fonts.googleapis.com" in link.get("href", "") or "fonts.gstatic.com" in link.get("href", "")
    )
    page["external_scripts_without_defer"] = sorted(
        script["src"] for script in parser.scripts
        if script.get("src")
        and "defer" not in script
        and "async" not in script
        and script.get("type", "").lower() != "module"
    )
    page["has_picture"] = parser.has_picture
    page["sources_count"] = len(parser.sources)

    page["title"] = clean_text("".join(parser.title_parts))
    page["title_length"] = len(page["title"])
    page["description"] = meta_content(parser.metas, "description")
    page["description_length"] = len(page["description"])
    page["lang"] = parser.lang
    page["has_viewport"] = parser.has_viewport
    page["robots_meta"] = meta_content(parser.metas, "robots")
    page["noindex"] = "noindex" in (page["robots_meta"] + " " + page["x_robots"]).lower()

    canonical = ""
    for link in parser.links:
        rel = link.get("rel", "").lower()
        if "canonical" in rel and link.get("href"):
            canonical = normalize_url(link["href"], final_url)
            break
    page["canonical"] = canonical

    page["headings"] = [{"level": int(tag[1]), "text": text} for tag, text in parser.headings]
    page["h1"] = [item["text"] for item in page["headings"] if item["level"] == 1]

    text = clean_text("".join(parser.text_parts))
    page["text_sample"] = text[:400]
    page["word_count"] = len(re.findall(r"\w+", text, re.UNICODE))

    images: list[dict[str, Any]] = []
    for image in parser.images:
        src = image.get("src") or image.get("data-src") or ""
        if not src:
            continue
        absolute = normalize_url(src, final_url)
        images.append(
            {
                "src": absolute,
                "alt_attr": "alt" in image,
                "alt": image.get("alt", ""),
                "width": image.get("width", ""),
                "height": image.get("height", ""),
                "srcset": image.get("srcset", ""),
                "loading": image.get("loading", ""),
                "fetchpriority": image.get("fetchpriority", ""),
                "in_picture": bool(image.get("_in_picture")),
            }
        )
    page["images"] = images
    page["images_missing_alt"] = sum(1 for image in images if not image["alt_attr"])
    page["images_missing_dimensions"] = sum(
        1 for image in images if not image["width"] or not image["height"]
    )

    internal: list[dict[str, str]] = []
    external = 0
    for anchor in parser.anchors:
        href = anchor["attrs"].get("href", "").strip()
        if not href or href.startswith("#") or href.lower().startswith(("mailto:", "tel:", "javascript:", "data:")):
            continue
        absolute = normalize_url(href, final_url)
        if not absolute.startswith(("http://", "https://")):
            continue
        if same_site(absolute, start_url):
            internal.append({"href": absolute, "text": anchor["text"], "rel": anchor["attrs"].get("rel", "")})
        else:
            external += 1
    page["internal_links"] = internal
    page["external_links"] = external

    parsed, jsonld_errors = parse_jsonld(parser.jsonld_raw)
    types: list[str] = []
    for item in parsed:
        collect_types(item, types)
    page["jsonld_types"] = sorted(set(types))
    page["jsonld_errors"] = jsonld_errors
    page["jsonld_expired_events"] = expired_event_nodes(parsed)

    faq_questions: list[str] = []
    for item in parsed:
        extract_faq_questions(item, faq_questions)
    faq_questions = list(dict.fromkeys(faq_questions))
    page["jsonld_faq_questions"] = faq_questions
    page["jsonld_faq_mismatches"] = [
        question for question in faq_questions
        if question.lower() not in text.lower()
    ]

    page["og"] = {
        meta.get("property", ""): clean_text(meta.get("content", ""))
        for meta in parser.metas
        if meta.get("property", "").lower().startswith("og:")
    }
    page["twitter"] = {
        meta.get("name", ""): clean_text(meta.get("content", ""))
        for meta in parser.metas
        if meta.get("name", "").lower().startswith("twitter:")
    }

    mixed: list[str] = []
    if final_url.startswith("https://"):
        resources = [image["src"] for image in images]
        resources += [script.get("src", "") for script in parser.scripts if script.get("src")]
        resources += [link.get("href", "") for link in parser.links if link.get("href")]
        resources += [frame.get("src", "") for frame in parser.iframes if frame.get("src")]
        mixed = sorted({resource for resource in resources if resource.lower().startswith("http://")})
    page["mixed_content"] = mixed

    security_names = [
        "strict-transport-security",
        "content-security-policy",
        "x-content-type-options",
        "referrer-policy",
        "permissions-policy",
    ]
    page["security_headers"] = {name: bool(header(headers, name)) for name in security_names}
    page["script_count"] = len(parser.scripts)
    return page


def add_issue(
    issues: list[dict[str, Any]],
    rule: str,
    severity: str,
    category: str,
    message: str,
    url: str,
    evidence: dict[str, Any],
    fix: str,
    docs: str = "",
    confidence: str = "confirmed",
) -> None:
    issues.append(
        {
            "rule": rule,
            "severity": severity,
            "category": category,
            "message": message,
            "url": url,
            "evidence": evidence,
            "fix": fix,
            "docs": docs,
            "confidence": confidence,
        }
    )


def page_issues(page: dict[str, Any], start_url: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    url = page["url"]
    status = page["status"]

    if page["error"]:
        severity = "critical" if url_key(url) == url_key(start_url) else "medium"
        add_issue(issues, "fetch-error", severity, "crawl",
                  "Seite konnte nicht geladen werden."
                  + ("" if severity == "critical" else " Netzwerk-/TLS-Fehler; vor dem Melden erneut pruefen."),
                  url, {"error": page["error"]}, "DNS, TLS, Firewall und Erreichbarkeit prüfen.")
        return issues
    if status is not None and status >= 400:
        severity = "critical" if url_key(url) == url_key(start_url) else "high"
        add_issue(issues, "http-status", severity, "crawl", f"HTTP-Status {status}.",
                  url, {"status": status}, "URL reparieren oder dauerhaft auf eine gültige Seite redirecten.")
        return issues
    if status is None:
        add_issue(issues, "http-status", "high", "crawl", "Kein HTTP-Status ermittelbar.",
                  url, {}, "Serverantwort prüfen.")
        return issues

    chain = page["redirect_chain"]
    if len(chain) > 2:
        add_issue(issues, "redirect-chain", "high", "crawl", f"Redirect-Kette mit {len(chain)} Sprüngen.",
                  url, {"chain": chain}, "Auf einen einzigen 301 auf das finale Ziel reduzieren.")
    elif len(chain) == 2:
        add_issue(issues, "redirect-chain", "medium", "crawl", "Redirect-Kette mit 2 Sprüngen.",
                  url, {"chain": chain}, "Zwischenschritt entfernen, direkt auf das Ziel verweisen.")

    path = urllib.parse.urlsplit(url).path or "/"
    legal_path = bool(LEGAL_NOINDEX.search(path))
    app_path = bool(APP_PATH.search(path))
    intentional_noindex = bool(page["noindex"] and (legal_path or app_path))
    csr_shell = bool(page["empty_shell"] and not page["noindex"])
    soft_context = intentional_noindex or csr_shell

    if not page["title"]:
        add_issue(issues, "title-missing", "info" if intentional_noindex else "high", "on-page", "Title fehlt.",
                  url, {}, "Eindeutigen Title mit Hauptkeyword und Marke setzen.")
    elif page["title_length"] < 30 or page["title_length"] > 60:
        add_issue(issues, "title-length", "info" if soft_context else "low", "on-page",
                  f"Title-Länge {page['title_length']} Zeichen (Ziel 30–60)."
                  + (" (CSR-Shell oder absichtlich noindex; gerendertes HTML prüfen.)" if soft_context else ""),
                  url, {"title": page["title"]}, "Title auf 30–60 Zeichen verdichten, Keyword vorne.")

    if page["title"]:
        title_parts = [part.lower() for part in re.split(r"[\W_]+", page["title"]) if part]
        if len(title_parts) >= 2 and title_parts[-1] == title_parts[-2]:
            add_issue(issues, "title-brand-duplicated", "info" if soft_context else "low", "on-page",
                      "Title endet mit doppeltem Marken-/Wort-Suffix.",
                      url, {"title": page["title"]}, "Marke nur einmal anhängen.")

    if not page["description"]:
        add_issue(issues, "description-missing", "info" if intentional_noindex else "medium", "on-page", "Meta-Description fehlt.",
                  url, {}, "Eindeutige Description mit Nutzen und CTA setzen.")
    elif page["description_length"] < 70 or page["description_length"] > 160:
        add_issue(issues, "description-length", "info" if soft_context else "low", "on-page",
                  f"Description-Länge {page['description_length']} Zeichen (Ziel 70–160)."
                  + (" (CSR-Shell oder absichtlich noindex.)" if soft_context else ""),
                  url, {"description": page["description"]}, "Description auf 70–160 Zeichen kürzen/erweitern.")

    if not page["h1"]:
        h1_severity = "info" if soft_context else "high"
        h1_message = "H1 fehlt."
        if csr_shell:
            h1_message = "H1 fehlt im Roh-HTML (CSR-Shell); gerendertes DOM prüfen oder vorrendern."
        elif intentional_noindex:
            h1_message = "H1 fehlt auf einer absichtlich noindex-Seite (App/Auth)."
        add_issue(issues, "h1-missing", h1_severity, "on-page", h1_message,
                  url, {}, "Genau eine inhaltliche H1 pro Seite setzen.")
    elif len(page["h1"]) > 1:
        add_issue(issues, "h1-multiple", "info" if soft_context else "medium", "on-page", f"{len(page['h1'])} H1 gefunden.",
                  url, {"h1": page["h1"]}, "Auf eine H1 reduzieren; Rest als H2/H3.")

    levels = [item["level"] for item in page["headings"]]
    for previous, current in zip(levels, levels[1:]):
        if current - previous > 1:
            add_issue(issues, "heading-order", "low", "on-page",
                      f"Heading-Sprung von H{previous} auf H{current}.",
                      url, {"levels": levels}, "Heading-Hierarchie lückenlos aufbauen.")
            break

    if page["canonical"]:
        canonical_key = url_key(page["canonical"])
        if host_key(page["canonical"]) == host_key(page["final_url"]) and netloc_key(page["canonical"]) != netloc_key(page["final_url"]):
            add_issue(issues, "canonical-host-alias", "medium", "indexing",
                      "Canonical nutzt www/non-www anders als die ausgelieferte URL.",
                      url, {"canonical": page["canonical"], "final_url": page["final_url"]},
                      "Canonical und finalen Host angleichen; der bevorzugte Host sollte direkt antworten, nicht per 301 auf den anderen zeigen.")
        elif canonical_key not in (url_key(page["final_url"]), url_key(start_url)):
            if host_key(page["canonical"]) != host_key(page["final_url"]):
                add_issue(issues, "canonical-cross-host", "high", "indexing",
                          "Canonical zeigt auf einen anderen Host.",
                          url, {"canonical": page["canonical"]}, "Canonical auf die eigene kanonische URL setzen.")
            else:
                add_issue(issues, "canonical-mismatch", "medium", "indexing",
                          "Canonical zeigt nicht auf diese URL.",
                          url, {"canonical": page["canonical"]}, "Canonical prüfen; bei Duplikaten bewusst setzen.")
    elif page["status"] and page["status"] < 400:
        add_issue(
            issues, "canonical-missing", "info" if soft_context else "medium", "indexing",
            "Canonical fehlt." + (" (CSR-Shell oder absichtlich noindex; gerendertes HTML prüfen.)" if soft_context else ""),
            url, {}, "Selbstreferenzierenden Canonical im Head setzen.",
        )

    if page["noindex"]:
        legal = legal_path
        if intentional_noindex:
            severity = "info"
            message = (
                "Rechtsseite ist noindex; meist beabsichtigt, Policy bestätigen."
                if legal
                else "Seite ist absichtlich noindex (App/Auth); nur bei versehentlicher Indexierung eingreifen."
            )
        else:
            severity = "high" if url_key(url) == url_key(start_url) else "medium"
            message = "Seite ist auf noindex gesetzt."
        add_issue(issues, "noindex", severity, "indexing", message,
                  url, {"robots": page["robots_meta"], "x_robots": page["x_robots"]},
                  "Nur beibehalten, wenn die Seite bewusst nicht indexiert werden soll.")

    if page["empty_shell"] and not page["noindex"]:
        add_issue(issues, "csr-shell", "high", "rendering",
                  "Das Roh-HTML enthält einen leeren App-Mount; der Inhalt entsteht erst im Browser.",
                  url, {"empty_shell": True, "scripts": page["script_count"]},
                  "Öffentliche Route server-rendern oder prerendern; interaktive Inseln dürfen clientseitig bleiben.",
                  confidence="confirmed")
    elif page["word_count"] < 50 and page["script_count"] >= 5 and not page["noindex"]:
        add_issue(issues, "csr-thin-shell", "medium", "rendering",
                  f"Nur {page['word_count']} Wörter im Roh-HTML bei {page['script_count']} Script-Tags.",
                  url, {"word_count": page["word_count"], "scripts": page["script_count"]},
                  "Prüfen, ob Inhalte erst nach Hydration entstehen; kritische Inhalte serverseitig ausliefern.",
                  confidence="likely")

    if page["hreflang"]:
        invalid = [item for item in page["hreflang"] if not valid_hreflang(item["hreflang"])]
        if invalid:
            add_issue(issues, "hreflang-invalid", "medium", "internationalization",
                      "Ungültige hreflang-Werte gefunden.",
                      url, {"invalid": invalid[:10]},
                      "ISO-639-1-Sprache plus optionale ISO-3166-1-Alpha-2-Region verwenden; x-default ist erlaubt.")
        self_refs = [
            item for item in page["hreflang"]
            if url_key(normalize_url(item["href"], url)) == url_key(url)
        ]
        if not self_refs:
            add_issue(issues, "hreflang-self-missing", "low", "internationalization",
                      "hreflang-Cluster enthält keinen Selbstverweis.",
                      url, {"hreflang": page["hreflang"][:10]},
                      "Jede Sprachversion soll sich selbst und alle anderen Versionen verlinken.")

    if page["images_missing_alt"]:
        add_issue(issues, "images-alt-missing", "medium", "content",
                  f"{page['images_missing_alt']} Bild(er) ohne alt-Attribut.",
                  url, {"count": page["images_missing_alt"]},
                  "Inhaltlich sinnvolle alt-Texte ergänzen; dekorative Bilder mit alt=\"\".")
    if page["images_missing_dimensions"]:
        add_issue(issues, "images-dimensions-missing", "low", "performance",
                  f"{page['images_missing_dimensions']} Bild(er) ohne width/height.",
                  url, {"count": page["images_missing_dimensions"]},
                  "width/height oder aspect-ratio setzen, um CLS zu vermeiden.")

    legal_path = bool(LEGAL_NOINDEX.search(urllib.parse.urlsplit(url).path or "/"))
    if page["word_count"] and page["word_count"] < 200:
        add_issue(issues, "thin-content", "info" if (legal_path or soft_context) else "medium", "content",
                  f"Nur {page['word_count']} Wörter sichtbarer Text.",
                  url, {"word_count": page["word_count"]}, "Inhaltlichen Mehrwert ergänzen oder Seite konsolidieren.")
    elif page["word_count"] and page["word_count"] < 300:
        add_issue(issues, "thin-content", "info" if soft_context else "low", "content",
                  f"{page['word_count']} Wörter sichtbarer Text (dünn).",
                  url, {"word_count": page["word_count"]}, "Inhalt prüfen und bei Bedarf ausbauen.")

    if page["status"] == 200 and not page["noindex"] and not csr_shell:
        marker = DRAFT_MARKERS.search(page.get("text_sample", ""))
        if marker and page["word_count"] < 150:
            add_issue(issues, "draft-indexable", "low", "content",
                      "Seite enthält Entwurfs-/Platzhaltertext und ist indexierbar.",
                      url, {"marker": marker.group(0), "word_count": page["word_count"]},
                      "Bis zur Fertigstellung noindex setzen und aus der Sitemap nehmen.")

    if not page["lang"]:
        add_issue(issues, "lang-missing", "low", "accessibility", "html-lang fehlt.",
                  url, {}, "Sprache im html-Tag setzen (z. B. lang=\"de\").")
    else:
        lang_prefix = re.match(r"/(de|en)(?:/|$)", urllib.parse.urlsplit(url).path or "/", re.I)
        if lang_prefix and page["lang"].split("-")[0].lower() != lang_prefix.group(1).lower():
            add_issue(
                issues, "lang-mismatch", "info" if intentional_noindex else "medium", "internationalization",
                f"html lang=\"{page['lang']}\" passt nicht zum URL-Sprachpräfix /{lang_prefix.group(1)}/.",
                url, {"lang": page["lang"], "path": urllib.parse.urlsplit(url).path},
                "html lang pro Sprache setzen; bei CSR nach dem Sprachwechsel aktualisieren oder serverseitig ausliefern.",
            )

    if not page["has_viewport"]:
        add_issue(issues, "viewport-missing", "high", "mobile", "Viewport-Meta fehlt.",
                  url, {}, "Meta viewport für mobile Darstellung ergänzen.")

    if page["jsonld_errors"]:
        add_issue(issues, "jsonld-invalid", "medium", "structured-data", "JSON-LD ist ungültig.",
                  url, {"errors": page["jsonld_errors"]}, "JSON-LD syntaktisch korrigieren und validieren.")
    elif not page["jsonld_types"]:
        add_issue(issues, "jsonld-missing", "info" if soft_context else "low", "structured-data", "Kein JSON-LD gefunden.",
                  url, {}, "Passendes Schema (Article, LocalBusiness, FAQPage …) ergänzen, nur wenn inhaltlich korrekt.")

    expired_events = page.get("jsonld_expired_events") or []
    if expired_events:
        add_issue(issues, "jsonld-event-expired", "medium", "structured-data",
                  f"{len(expired_events)} Event(s) im JSON-LD sind abgelaufen, stehen aber auf 'scheduled'.",
                  url, {"events": expired_events[:5]},
                  "Vergangene Events entfernen oder eventStatus auf EventCancelled/EventPostponed setzen; nur kommende Events als scheduled auszeichnen.")

    if not page["og"]:
        add_issue(issues, "og-missing", "info" if soft_context else "low", "social", "Keine Open-Graph-Tags.",
                  url, {}, "og:title, og:description, og:image, og:url ergänzen.")
    if not page["twitter"]:
        add_issue(issues, "twitter-missing", "info" if soft_context else "low", "social", "Keine Twitter-Card-Tags.",
                  url, {}, "twitter:card, twitter:title, twitter:description ergänzen.")

    if page["mixed_content"]:
        add_issue(issues, "mixed-content", "high", "security", "HTTP-Ressourcen auf einer HTTPS-Seite.",
                  url, {"resources": page["mixed_content"]}, "Alle Ressourcen über HTTPS laden.")

    missing_headers = [name for name, present in page["security_headers"].items() if not present]
    if missing_headers:
        severity = "medium" if "strict-transport-security" in missing_headers else "low"
        add_issue(issues, "security-headers", severity, "security",
                  f"Security-Header fehlen: {', '.join(missing_headers)}.",
                  url, {"missing": missing_headers}, "Header serverseitig ergänzen (HSTS, CSP, nosniff, Referrer-Policy).")

    if page["html_bytes"] > 500_000:
        add_issue(issues, "html-size", "low", "performance",
                  f"HTML ist {round(page['html_bytes'] / 1024)} KB groß.",
                  url, {"bytes": page["html_bytes"]}, "Markup reduzieren, Inhalte auslagern.")
    if page["script_count"] > 30:
        add_issue(issues, "scripts-many", "low", "performance",
                  f"{page['script_count']} Script-Tags gefunden.",
                  url, {"count": page["script_count"]}, "Unnötige Scripts entfernen, laden deferren.")
    if page["response_time_ms"] > 1500:
        add_issue(issues, "slow-response", "low", "performance",
                  f"Serverantwort {page['response_time_ms']} ms (eine Messung; kann Cold-Start sein).",
                  url, {"response_time_ms": page["response_time_ms"]}, "TTFB prüfen (Hosting, Cache, DB).")

    if page["status"] and page["status"] < 400 and not page["internal_links"] and url_key(url) != url_key(start_url):
        add_issue(issues, "internal-links-none", "info" if soft_context else "medium", "internal-linking",
                  "Keine internen Links auf dieser Seite."
                  + (" (CSR-Shell oder absichtlich noindex.)" if soft_context else ""),
                  url, {}, "Auf relevante Seiten verlinken und von dort zurückverlinken.")
    return issues


def site_issues(
    pages: list[dict[str, Any]],
    start_url: str,
    robots: Robots,
    robots_result: dict[str, Any],
    sitemap: dict[str, Any],
    llms_status: int | None,
    user_agent: str,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    if robots_result["status"] is None or (robots_result["status"] or 0) >= 500:
        add_issue(issues, "robots-unavailable", "medium", "crawl", "robots.txt nicht erreichbar (5xx/Netzwerk).",
                  start_url, {"status": robots_result["status"], "error": robots_result["error"]},
                  "robots.txt mit Sitemap-Verweis unter der Domainwurzel ausliefern.")

    if not robots.is_allowed(start_url, user_agent):
        add_issue(issues, "robots-blocks-start", "critical", "crawl", "Start-URL ist per robots.txt blockiert.",
                  start_url, {"robots": robots.text[:1000]}, "Regel prüfen und die Startseite freigeben.")

    if not sitemap["urls"]:
        add_issue(issues, "sitemap-missing", "medium", "indexing", "Keine Sitemap-URLs gefunden.",
                  start_url, {"errors": sitemap["errors"]}, "XML-Sitemap erzeugen und in robots.txt verlinken.")
    else:
        start_key = url_key(start_url)
        if start_key not in {url_key(url) for url in sitemap["urls"]}:
            add_issue(issues, "sitemap-start-missing", "medium", "indexing",
                      "Start-URL fehlt in der Sitemap.",
                      start_url, {"sitemap_count": len(sitemap["urls"])}, "Startseite in die Sitemap aufnehmen.")
        start_page = next((page for page in pages if url_key(page["url"]) == url_key(start_url)), None)
        final_netloc = netloc_key(start_page["final_url"] if start_page else start_url)
        sitemap_netlocs = {netloc_key(url) for url in sitemap["urls"]}
        alias_hosts = {
            host for host in sitemap_netlocs - {final_netloc}
            if host.startswith("www.") or final_netloc.startswith("www.")
        }
        cross_hosts = sitemap_netlocs - {final_netloc} - alias_hosts
        if alias_hosts:
            add_issue(issues, "sitemap-host-alias", "medium", "indexing",
                      "Sitemap listet URLs mit www/non-www anders als der finale Host.",
                      start_url, {"sitemap_hosts": sorted(alias_hosts), "final_host": final_netloc},
                      "Sitemap-URLs auf den Host umstellen, der ohne Redirect antwortet.")
        if cross_hosts:
            add_issue(issues, "sitemap-cross-host", "high", "indexing",
                      "Sitemap enthaelt URLs eines anderen Hosts.",
                      start_url, {"sitemap_hosts": sorted(cross_hosts), "final_host": final_netloc},
                      "Nur URLs der eigenen kanonischen Domain in die Sitemap aufnehmen.")
        for sitemap_url in robots.sitemaps:
            if netloc_key(sitemap_url) == final_netloc:
                continue
            add_issue(issues, "robots-sitemap-host-alias", "low", "indexing",
                      "robots.txt verweist auf eine Sitemap unter einem anderen Host.",
                      start_url, {"sitemap": sitemap_url, "final_host": final_netloc},
                      "Sitemap-Verweis auf den finalen Host umstellen.")
    for error in sitemap["errors"]:
        add_issue(issues, "sitemap-invalid", "high", "indexing", "Sitemap konnte nicht gelesen werden.",
                  start_url, {"error": error}, "Sitemap als valides XML mit absoluten URLs ausliefern.")

    if sitemap["urls"]:
        sitemap_keys = {url_key(url) for url in sitemap["urls"]}
        for page in pages:
            if page["noindex"] and url_key(page["url"]) in sitemap_keys:
                add_issue(issues, "sitemap-noindex-urls", "medium", "indexing",
                          "noindex-URL ist in der Sitemap.",
                          page["url"], {"robots": page["robots_meta"]},
                          "noindex-Seiten aus der Sitemap entfernen; Sitemaps sollen indexierbare URLs enthalten.")
        if not robots.sitemaps:
            add_issue(issues, "robots-no-sitemap", "low", "crawl",
                      "robots.txt enthält keinen Sitemap-Verweis.",
                      start_url, {"sitemap_count": len(sitemap["urls"])},
                      "Sitemap in robots.txt mit absoluter URL verlinken.")

    if llms_status is None or llms_status >= 400:
        add_issue(issues, "llms-txt-optional", "info", "ai-search",
                  "llms.txt fehlt (optional; Google Search ignoriert die Datei).",
                  start_url, {"status": llms_status},
                  "Nur für andere Agenten/Verzeichnisse anlegen, wenn es einen konkreten Nutzen gibt; kein Google-SEO-Signal.")

    for bot in AI_BOTS:
        if not robots.is_allowed(start_url, bot):
            add_issue(issues, "ai-bot-blocked", "info", "ai-search", f"{bot} ist per robots.txt blockiert.",
                      start_url, {"bot": bot}, "Nur beibehalten, wenn AI-Crawler bewusst ausgeschlossen werden sollen.")

    titles: dict[str, list[str]] = {}
    descriptions: dict[str, list[str]] = {}
    for page in pages:
        if page["noindex"]:
            continue
        if page["title"]:
            titles.setdefault(page["title"].lower(), []).append(page["url"])
        if page["description"]:
            descriptions.setdefault(page["description"].lower(), []).append(page["url"])
    for title, urls in titles.items():
        if len(urls) > 1:
            all_csr = all(
                page.get("empty_shell") for page in pages if page["url"] in urls
            )
            add_issue(
                issues, "duplicate-title", "medium" if all_csr else "high", "on-page",
                "Mehrere Seiten haben denselben Title."
                + (" (CSR-Shell; gerenderte Titles prüfen.)" if all_csr else ""),
                urls[0], {"title": title, "urls": urls}, "Pro Seite einen eindeutigen Title setzen.",
            )
    for description, urls in descriptions.items():
        if len(urls) > 1:
            all_csr = all(
                page.get("empty_shell") for page in pages if page["url"] in urls
            )
            add_issue(issues, "duplicate-description", "info" if all_csr else "medium", "on-page",
                      "Mehrere Seiten haben dieselbe Description."
                      + (" (CSR-Shell.)" if all_csr else ""),
                      urls[0], {"description": description, "urls": urls}, "Pro Seite eine eigene Description setzen.")

    crawled = {url_key(page["url"]): page["url"] for page in pages}
    page_by_url = {url_key(page["url"]): page for page in pages}
    inbound: dict[str, int] = {key: 0 for key in crawled}
    for page in pages:
        for link in page["internal_links"]:
            key = url_key(link["href"])
            if key in inbound and key != url_key(page["url"]):
                inbound[key] += 1
    for key, url in crawled.items():
        if key != url_key(start_url) and host_key(url) != host_key(start_url):
            continue
        if key != url_key(start_url) and inbound.get(key, 0) == 0:
            page = page_by_url.get(key) or {}
            soft = bool(page.get("empty_shell") or page.get("noindex"))
            add_issue(issues, "orphan-page", "info" if soft else "medium", "internal-linking",
                      "Seite hat keinen eingehenden internen Link im Crawl."
                      + (" (CSR-Shell oder absichtlich noindex.)" if soft else ""),
                      url, {"inbound": 0}, "Von relevanten Seiten verlinken oder aus der Sitemap entfernen.")
    return issues


def not_found_issues(result: dict[str, Any] | None, start_url: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if result is None:
        return issues
    status = result["status"]
    if status is None or status >= 500:
        add_issue(issues, "not-found-unreachable", "medium", "indexing",
                  "Unbekannte URL konnte nicht geprüft werden.",
                  start_url, {"status": status, "error": result["error"]},
                  "Fehlerroute und Serverantwort prüfen.")
    elif status == 200:
        add_issue(issues, "soft-404", "high", "indexing",
                  "Unbekannte URL liefert HTTP 200 statt 404.",
                  start_url, {"status": status},
                  "Unbekannte Routen mit echtem 404/410 beantworten; kein SPA-Fallback auf eine 200-Seite.",
                  confidence="confirmed")
    elif status not in (404, 410):
        add_issue(issues, "not-found-status", "medium", "indexing",
                  f"Unbekannte URL liefert HTTP {status} statt 404/410.",
                  start_url, {"status": status},
                  "Statuscode der Fehlerroute korrigieren.", confidence="confirmed")
    return issues


def host_alias_issues(start_url: str, fetch_cached) -> list[dict[str, Any]]:
    """Flag a www/non-www alias that serves 200 without redirecting to the canonical host."""
    issues: list[dict[str, Any]] = []
    parts = urllib.parse.urlsplit(start_url)
    host = (parts.hostname or "").lower()
    if not host or host in ("localhost", "127.0.0.1") or ":" in host:
        return issues
    alias_host = host[4:] if host.startswith("www.") else "www." + host
    try:
        port = parts.port
    except ValueError:
        port = None
    netloc = f"{alias_host}:{port}" if port and port not in (80, 443) else alias_host
    alias_url = urllib.parse.urlunsplit((parts.scheme, netloc, parts.path or "/", parts.query, ""))
    result = fetch_cached(alias_url)
    status = result["status"]
    if status is None or status >= 400:
        return issues
    final_url = result["final_url"] or alias_url
    if netloc_key(final_url) == netloc_key(start_url):
        return issues
    if netloc_key(final_url) == netloc_key(alias_url):
        add_issue(
            issues, "host-alias-200", "medium", "indexing",
            f"Der Host-Alias {alias_host} liefert HTTP 200 ohne Redirect auf den kanonischen Host.",
            alias_url, {"alias": alias_url, "final_url": final_url, "status": status},
            "Alias per 301 auf den kanonischen Host umleiten oder selbstreferenzierendes Canonical auf beiden Hosts ausliefern.",
        )
    return issues


def compute_score(issues: list[dict[str, Any]]) -> int:
    per_rule: dict[str, int] = {}
    for issue in issues:
        weight = SEVERITY_WEIGHT.get(issue["severity"], 1)
        per_rule[issue["rule"]] = per_rule.get(issue["rule"], 0) + weight
    penalty = sum(min(value, 20) for value in per_rule.values())
    return max(0, 100 - penalty)


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
                "count": 0,
                "urls": [],
            },
        )
        item["count"] += 1
        if issue["url"] not in item["urls"]:
            item["urls"].append(issue["url"])
    return sorted(
        grouped.values(),
        key=lambda item: (-SEVERITY_WEIGHT.get(item["severity"], 1), -item["count"], item["rule"]),
    )


def table_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    site = report["site"]
    grouped = report["top_issues"]
    pages = report["pages"]
    lines: list[str] = []
    lines.append(f"# SEO Audit — {report['start_url']}")
    lines.append("")
    lines.append(f"Generated: `{report['generated_at']}` · Tool: `{TOOL_NAME} {VERSION}`")
    lines.append("")
    lines.append(f"**Score: {summary['score']}/100** · Pages crawled: "
                 f"{summary['pages_crawled']}/{report['config']['max_pages']} · "
                 f"Issues: {summary['issue_count']}")
    lines.append("")
    coverage = summary.get("coverage") or {}
    if coverage.get("note"):
        lines.append(f"> Coverage: {coverage['note']}")
        lines.append("")
    if summary["limit_reached"]:
        lines.append("> Page limit reached. The audit is a sample, not a full inventory.")
        lines.append("")

    lines.append("## Executive summary")
    lines.append("")
    counts = summary["issues_by_severity"]
    lines.append(
        f"Critical: **{counts.get('critical', 0)}** · High: **{counts.get('high', 0)}** · "
        f"Medium: **{counts.get('medium', 0)}** · Low: **{counts.get('low', 0)}**"
    )
    lines.append("")
    if grouped:
        lines.append("The highest-leverage fixes are listed first. Every finding is backed by "
                     "evidence in `report.json`; treat the list as a prioritized work queue, "
                     "not as a complete index of Google.")
    else:
        lines.append("No findings in the crawled sample. That is not proof of perfect SEO; "
                     "check JavaScript rendering, field data and Search Console.")
    lines.append("")

    lines.append("## Top issues")
    lines.append("")
    lines.append("| # | Severity | Issue | Affected | Fix |")
    lines.append("|---:|---|---|---:|---|")
    for index, item in enumerate(grouped[:15], start=1):
        lines.append(
            f"| {index} | {item['severity']} | {table_cell(item['message'])} | "
            f"{item['count']} | {table_cell(item['fix'])} |"
        )
    lines.append("")

    lines.append("## Pages")
    lines.append("")
    lines.append("| URL | Status | Title | Desc | H1 | Words | Issues |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for page in pages:
        page_issue_count = len(page["issues"])
        lines.append(
            f"| {table_cell(page['url'])} | {page['status'] or '—'} | "
            f"{page['title_length']} | {page['description_length']} | "
            f"{len(page['h1'])} | {page['word_count']} | {page_issue_count} |"
        )
    lines.append("")

    lines.append("## Page details")
    lines.append("")
    for page in pages:
        if not page["issues"] and page["status"] and page["status"] < 400:
            continue
        lines.append(f"### {page['url']}")
        lines.append("")
        lines.append(f"- Status: `{page['status']}` · Final: `{page['final_url']}`")
        lines.append(f"- Title: {page['title'] or '—'}")
        lines.append(f"- Description: {page['description'] or '—'}")
        lines.append(f"- Canonical: `{page['canonical'] or '—'}`")
        lines.append(f"- H1: {page['h1'][0] if page['h1'] else '—'}")
        lines.append(f"- Words: {page['word_count']} · Images: {len(page['images'])} "
                     f"(missing alt: {page['images_missing_alt']})")
        lines.append(f"- JSON-LD: {', '.join(page['jsonld_types']) or '—'}")
        if page["redirect_chain"]:
            chain = " → ".join(f"{item['status']} {item['url']}" for item in page["redirect_chain"])
            lines.append(f"- Redirects: {chain}")
        if page["issues"]:
            lines.append("")
            lines.append("| Severity | Rule | Evidence | Fix |")
            lines.append("|---|---|---|---|")
            for issue in page["issues"]:
                evidence = json.dumps(issue["evidence"], ensure_ascii=False)[:220]
                lines.append(
                    f"| {issue['severity']} | `{issue['rule']}` | {table_cell(evidence)} | "
                    f"{table_cell(issue['fix'])} |"
                )
        lines.append("")

    lines.append("## Site checks")
    lines.append("")
    lines.append(f"- robots.txt: HTTP `{site['robots_status']}` · Sitemaps: "
                 f"{len(site['sitemaps']) or '—'}")
    lines.append(f"- Sitemap URLs: {site['sitemap_count']} · Errors: {len(site['sitemap_errors'])}")
    lines.append(f"- llms.txt: {'found' if site['llms_found'] else 'not found (optional; Google Search ignores it)'}")
    if site.get("not_found_status") is not None:
        lines.append(f"- Unknown-URL check: HTTP `{site['not_found_status']}`")
    bot_parts = [f"{key}={'allowed' if value else 'blocked'}" for key, value in site["ai_bots"].items()]
    lines.append("- AI bots: " + ", ".join(bot_parts))
    lines.append("")

    lines.append("## Method and limits")
    lines.append("")
    lines.append("- Static HTML only; no JavaScript rendering in the crawl step.")
    lines.append("- Same-site crawl, robots.txt respected, page cap applies.")
    lines.append("- No Google SERP scraping, no backlink index, no rank tracking.")
    lines.append("- No field Core Web Vitals; use CrUX/PSI separately.")
    lines.append("- A crawl is not an index. Findings are evidence, not a ranking promise.")
    lines.append("")

    lines.append("## Next 30/60/90")
    lines.append("")
    lines.append("1. **0–30 days:** fix critical/high crawl, indexing and canonical issues; "
                 "repair redirects and sitemap.")
    lines.append("2. **30–60 days:** titles/descriptions, H1/heading structure, internal links, "
                 "image alt/dimensions, thin content.")
    lines.append("3. **60–90 days:** performance, structured data, content quality, "
                 "measurement against Search Console. AI features need no special file; "
                 "normal SEO is the requirement.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_csv(report: dict[str, Any], path: Path) -> None:
    fields = [
        "url", "status", "final_url", "title", "title_length", "description_length",
        "h1_count", "word_count", "canonical", "noindex", "images_missing_alt",
        "internal_links", "jsonld_types", "response_time_ms", "issues",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for page in report["pages"]:
            writer.writerow(
                {
                    "url": page["url"],
                    "status": page["status"],
                    "final_url": page["final_url"],
                    "title": page["title"],
                    "title_length": page["title_length"],
                    "description_length": page["description_length"],
                    "h1_count": len(page["h1"]),
                    "word_count": page["word_count"],
                    "canonical": page["canonical"],
                    "noindex": page["noindex"],
                    "images_missing_alt": page["images_missing_alt"],
                    "internal_links": len(page["internal_links"]),
                    "jsonld_types": ";".join(page["jsonld_types"]),
                    "response_time_ms": page["response_time_ms"],
                    "issues": ";".join(issue["rule"] for issue in page["issues"]),
                }
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evidence-based static SEO scanner")
    parser.add_argument("url", help="Start URL")
    parser.add_argument("--max-pages", type=int, default=25)
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--out", default="seo-report")
    parser.add_argument("--user-agent", default=DEFAULT_UA)
    parser.add_argument("--ignore-robots", action="store_true",
                        help="Only for sites you own. Disables robots checks.")
    parser.add_argument("--insecure", action="store_true",
                        help="Skip TLS certificate verification. Only for your own hosts.")
    parser.add_argument("--no-sitemap", action="store_true")
    parser.add_argument("--no-404-check", action="store_true",
                        help="Skip the unknown-URL soft-404 probe.")
    parser.add_argument("--include-url", action="append", default=[],
                        help="Extra URL to crawl even if unlinked; repeatable, robots still applies.")
    parser.add_argument("--include-host", action="append", default=[],
                        help="Additional host to crawl (e.g. app.example.com); repeatable, robots still applies.")
    parser.add_argument("--max-html-kb", type=int, default=2048)
    args = parser.parse_args(argv)

    start_url = normalize_url(args.url)
    if not start_url.startswith(("http://", "https://")):
        print("URL must start with http:// or https://", file=sys.stderr)
        return 2
    extra_hosts: set[str] = set()
    extra_host_urls: list[str] = []
    for value in args.include_host:
        candidate = value.strip()
        if not candidate:
            continue
        if not candidate.startswith(("http://", "https://")):
            candidate = "https://" + candidate
        if urllib.parse.urlsplit(candidate).hostname:
            extra_hosts.add(host_key(candidate))
            extra_host_urls.append(candidate.rstrip("/") + "/")

    def allowed(url: str) -> bool:
        return same_site(url, start_url) or host_key(url) in extra_hosts

    max_bytes = max(64, args.max_html_kb) * 1024
    cache: dict[str, dict[str, Any]] = {}

    def fetch_cached(url: str) -> dict[str, Any]:
        key = url_key(url)
        if key not in cache:
            cache[key] = fetch(url, args.timeout, args.user_agent, max_bytes, args.insecure)
        return cache[key]

    parts = urllib.parse.urlsplit(start_url)
    base = f"{parts.scheme}://{parts.netloc}"
    robots_result = fetch_cached(base + "/robots.txt")
    robots_text = decode_body(robots_result["body"], robots_result["headers"]) if robots_result["body"] else ""
    robots = Robots(robots_text)

    if not args.ignore_robots and not robots.is_allowed(start_url, args.user_agent):
        print(f"robots.txt blocks the start URL: {start_url}", file=sys.stderr)
        return 3

    sitemap = {"urls": [], "errors": [], "sitemaps": []}
    if not args.no_sitemap:
        sitemap = collect_sitemaps(start_url, robots, fetch_cached, max_urls=max(100, args.max_pages * 20))
    sitemap_urls = [url for url in sitemap["urls"] if same_site(url, start_url)]

    llms_result = fetch_cached(base + "/llms.txt")
    llms_status = llms_result["status"]
    not_found_result: dict[str, Any] | None = None
    if not args.no_404_check:
        not_found_result = fetch_cached(f"{base}/__seo-audit-404-{int(time.time())}")

    queue: deque[tuple[str, int]] = deque([(start_url, 0)])
    for url in sitemap_urls[: max(10, args.max_pages * 2)]:
        if not should_skip(url):
            queue.append((url, 1))
    for extra in args.include_url:
        queue.append((normalize_url(extra, start_url), 1))
    for extra in extra_host_urls:
        queue.append((extra, 1))

    visited: set[str] = set()
    pages: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    all_issues: list[dict[str, Any]] = []
    delay = max(0.0, min(robots.crawl_delay(args.user_agent) or 0.2, 2.0))
    limit_reached = False

    while queue and len(pages) < args.max_pages:
        url, depth = queue.popleft()
        key = url_key(url)
        if key in visited:
            continue
        visited.add(key)
        if not allowed(url):
            continue
        if url_key(url) != url_key(start_url) and should_skip(url):
            continue
        if not args.ignore_robots and not robots.is_allowed(url, args.user_agent):
            continue

        result = fetch_cached(url)
        content_type_ok = is_html(result["headers"])
        parser: PageParser | None = None
        if content_type_ok and result["body"]:
            parser = PageParser()
            try:
                parser.feed(decode_body(result["body"], result["headers"]))
            except Exception as exc:  # noqa: BLE001 - malformed HTML is an edge case
                parser = None
                all_issues.append(
                    {
                        "rule": "html-parse-error",
                        "severity": "low",
                        "category": "crawl",
                        "message": f"HTML konnte nicht geparst werden: {exc}",
                        "url": url,
                        "evidence": {},
                        "fix": "Markup validieren.",
                        "docs": "",
                        "confidence": "confirmed",
                    }
                )
        if parser is None and result["status"] and result["status"] < 400:
            # Non-HTML resources are not pages; do not count them.
            if url_key(url) == url_key(start_url):
                print(f"Start URL is not HTML: {result['headers'].get('content-type', '')}", file=sys.stderr)
                return 4
            continue

        page = build_page(url, result, parser, start_url)
        page_issues_list = page_issues(page, start_url)
        page["issues"] = page_issues_list
        pages.append(page)
        issues.extend(page_issues_list)

        if parser is not None and depth < args.max_depth:
            for link in page["internal_links"]:
                if url_key(link["href"]) not in visited and not should_skip(link["href"]) and allowed(link["href"]):
                    if len(queue) + len(pages) < args.max_pages * 4:
                        queue.append((link["href"], depth + 1))
        if delay:
            time.sleep(delay)

    limit_reached = bool(queue)
    if sitemap["urls"]:
        if len(pages) < len(sitemap["urls"]):
            coverage_note = f"{len(pages)} of {len(sitemap['urls'])} sitemap URLs crawled (page cap, depth or robots)."
        elif len(pages) > len(sitemap["urls"]):
            coverage_note = f"All {len(sitemap['urls'])} sitemap URLs crawled; {len(pages) - len(sitemap['urls'])} more pages via internal links."
        else:
            coverage_note = f"All {len(sitemap['urls'])} sitemap URLs crawled."
    else:
        coverage_note = "No sitemap URLs; crawl followed internal links only."
    if extra_hosts:
        coverage_note += f" Included hosts: {', '.join(sorted(extra_hosts))}."

    canonical_issues: list[dict[str, Any]] = []
    checked_canonicals: set[str] = set()
    for page in pages:
        canonical = page["canonical"]
        if not canonical:
            continue
        target = normalize_url(canonical, page["final_url"])
        if not allowed(target):
            continue
        key = url_key(target)
        if key in checked_canonicals:
            continue
        if len(checked_canonicals) >= 25:
            break
        checked_canonicals.add(key)
        target_result = fetch_cached(target)
        status = target_result["status"]
        if status is None or status >= 500:
            severity = "medium"
        elif status >= 400:
            severity = "info" if (page["status"] or 200) >= 400 else "high"
        else:
            severity = ""
        if severity:
            add_issue(
                canonical_issues, "canonical-target-status", severity, "indexing",
                f"Canonical points to HTTP {status}.",
                page["url"], {"canonical": canonical, "status": status},
                "Canonical must resolve to a 200 URL; point it at the live page or remove it.",
            )
        elif target_result["final_url"] and url_key(target_result["final_url"]) != key:
            add_issue(
                canonical_issues, "canonical-target-redirect", "low", "indexing",
                "Canonical target redirects to another URL.",
                page["url"], {"canonical": canonical, "final_url": target_result["final_url"]},
                "Point the canonical directly at the final URL to avoid a redirect hop.",
            )

    site_issue_list = site_issues(pages, start_url, robots, robots_result, sitemap, llms_status, args.user_agent)
    site_issue_list += host_alias_issues(
        start_url,
        lambda url: fetch(url, args.timeout, args.user_agent, max_bytes, args.insecure),
    )
    site_issue_list += not_found_issues(not_found_result, start_url)
    all_issues = issues + site_issue_list + canonical_issues + all_issues
    grouped = group_issues(all_issues)
    counts: dict[str, int] = {}
    for issue in all_issues:
        counts[issue["severity"]] = counts.get(issue["severity"], 0) + 1

    report = {
        "tool": {"name": TOOL_NAME, "version": VERSION},
        "start_url": start_url,
        "generated_at": now_iso(),
        "config": {
            "max_pages": args.max_pages,
            "max_depth": args.max_depth,
            "timeout": args.timeout,
            "ignore_robots": args.ignore_robots,
            "no_sitemap": args.no_sitemap,
            "no_404_check": args.no_404_check,
            "include_url": args.include_url,
            "include_host": args.include_host,
            "user_agent": args.user_agent,
        },
        "summary": {
            "score": compute_score(all_issues),
            "pages_crawled": len(pages),
            "issue_count": len(all_issues),
            "issues_by_severity": counts,
            "limit_reached": limit_reached,
            "coverage": {
                "sitemap_urls": len(sitemap["urls"]),
                "crawled": len(pages),
                "note": coverage_note,
            },
        },
        "site": {
            "robots_status": robots_result["status"],
            "sitemaps": sitemap["sitemaps"],
            "sitemap_count": len(sitemap["urls"]),
            "sitemap_errors": sitemap["errors"],
            "llms_status": llms_status,
            "llms_found": bool(llms_status and llms_status < 400),
            "not_found_status": not_found_result["status"] if not_found_result else None,
            "rendering": {
                "empty_shell_pages": sum(1 for page in pages if page.get("empty_shell")),
                "thin_shell_pages": sum(1 for page in pages if page["word_count"] < 50 and page["script_count"] >= 5),
            },
            "ai_bots": {bot: robots.is_allowed(start_url, bot) for bot in AI_BOTS},
        },
        "top_issues": grouped,
        "pages": pages,
        "issues": all_issues,
    }

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_markdown(report, out_dir / "report.md")
    write_csv(report, out_dir / "pages.csv")

    print(f"Score {report['summary']['score']}/100 · "
          f"{len(pages)} pages · {len(all_issues)} issues")
    print(f"Report: {out_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
