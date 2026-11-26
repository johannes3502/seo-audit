from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT if (ROOT / "SKILL.md").exists() else Path(
    os.environ.get("SEO_AUDIT_SKILL", Path.home() / ".kilo" / "skills" / "seo-audit")
)
SCANNER = SKILL_ROOT / "scripts" / "seo_scan.py"

spec = importlib.util.spec_from_file_location("seo_scan", SCANNER)
assert spec and spec.loader
seo_scan = importlib.util.module_from_spec(spec)
sys.modules["seo_scan"] = seo_scan
spec.loader.exec_module(seo_scan)

INDEX = """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Beispielseite — Beratung für Tests</title>
  <meta name="description" content="Eine ausreichend lange Beschreibung für den Test der Beispielseite mit Nutzen und klarer Aussage.">
  <link rel="canonical" href="{base}/">
  <meta property="og:title" content="Beispielseite">
  <meta property="og:description" content="Beschreibung">
  <meta property="og:image" content="{base}/og.jpg">
  <meta property="og:url" content="{base}/">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Beispielseite">
  <meta name="twitter:description" content="Beschreibung">
  <link rel="preload" as="font" href="/font.woff2" crossorigin>
  <style data-seo-inline-css>body{{font-family:system-ui;margin:0}}h1{{font-size:2rem}}</style>
  <script type="application/ld+json">
  {{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{{"@type":"Question","name":"Was kostet das?","acceptedAnswer":{{"@type":"Answer","text":"Ein fairer Preis."}}}}]}}
  </script>
</head>
<body>
  <h1>Beispielseite für den Test</h1>
  <p>Dies ist ein ausreichend langer Text für den statischen Scanner. Er enthält mehrere Sätze, damit die Wortzählung nicht als dünner Inhalt gewertet wird.</p>
  <a href="/about.html">Über uns</a>
  <a href="/csr.html">CSR-Test</a>
  <a href="/canon.html">Canonical-Test</a>
  <img src="/img.jpg" width="640" height="360">
</body>
</html>
"""

CSR = """<!doctype html>
<html lang="de">
<head><title>CSR Testseite</title></head>
<body><div id="root"></div><script src="/app.js"></script></body>
</html>
"""

ABOUT = """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Beispielseite — Beratung für Tests</title>
</head>
<body>
  <p>Kurzer Text.</p>
  <a href="/">Start</a>
  <img src="/img.jpg">
</body>
</html>
"""

CANON = """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Canonical-Testseite — Beratung für Tests</title>
  <link rel="canonical" href="{base}/missing.html">
</head>
<body>
  <h1>Canonical-Testseite</h1>
  <p>Diese Seite zeigt absichtlich auf eine nicht existierende kanonische URL, damit der Scanner den Zielstatus prüft.</p>
  <a href="/">Start</a>
</body>
</html>
"""


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A002
        pass


class ScannerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.webroot = Path(cls.temp.name) / "site"
        cls.webroot.mkdir()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), lambda *a, **kw: QuietHandler(*a, directory=str(cls.webroot), **kw))
        cls.port = cls.server.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        (cls.webroot / "index.html").write_text(INDEX.format(base=cls.base), encoding="utf-8")
        (cls.webroot / "about.html").write_text(ABOUT, encoding="utf-8")
        (cls.webroot / "csr.html").write_text(CSR, encoding="utf-8")
        (cls.webroot / "canon.html").write_text(CANON.format(base=cls.base), encoding="utf-8")
        (cls.webroot / "robots.txt").write_text(
            f"User-agent: *\nAllow: /\nSitemap: {cls.base}/sitemap.xml\n", encoding="utf-8"
        )
        (cls.webroot / "sitemap.xml").write_text(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{cls.base}/</loc></url>
  <url><loc>{cls.base}/about.html</loc></url>
</urlset>""",
            encoding="utf-8",
        )
        (cls.webroot / "llms.txt").write_text(
            f"# Example\n- [Start]({cls.base}/)\n- [About]({cls.base}/about.html)\n",
            encoding="utf-8",
        )
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.temp.cleanup()

    def run_scan(self) -> dict:
        out = Path(self.temp.name) / "report"
        code = seo_scan.main(
            [
                self.base + "/",
                "--max-pages", "5",
                "--max-depth", "1",
                "--timeout", "5",
                "--out", str(out),
            ]
        )
        self.assertEqual(code, 0)
        return json.loads((out / "report.json").read_text(encoding="utf-8"))

    def test_generic_scan_finds_expected_issues(self) -> None:
        report = self.run_scan()
        rules = {issue["rule"] for issue in report["issues"]}
        self.assertGreaterEqual(report["summary"]["pages_crawled"], 2)
        self.assertIn("duplicate-title", rules)
        self.assertIn("images-alt-missing", rules)
        self.assertIn("h1-missing", rules)
        self.assertIn("canonical-target-status", rules)
        self.assertGreaterEqual(report["site"]["sitemap_count"], 2)
        self.assertLess(report["summary"]["score"], 100)
        self.assertIn("coverage", report["summary"])
        self.assertGreaterEqual(report["summary"]["coverage"]["sitemap_urls"], 2)

    def test_expired_event_nodes(self) -> None:
        nodes = [{
            "@type": "Event",
            "name": "Old festival",
            "startDate": "2025-09-01",
            "endDate": "2025-09-03",
            "eventStatus": "https://schema.org/EventScheduled",
        }]
        expired = seo_scan.expired_event_nodes(nodes, seo_scan.datetime(2026, 11, 25, tzinfo=seo_scan.timezone.utc))
        self.assertEqual(len(expired), 1)
        current = seo_scan.expired_event_nodes(
            [{"@type": "Event", "endDate": "2027-01-01"}],
            seo_scan.datetime(2026, 11, 25, tzinfo=seo_scan.timezone.utc),
        )
        self.assertEqual(current, [])

    def test_legal_noindex_pattern(self) -> None:
        self.assertTrue(seo_scan.LEGAL_NOINDEX.search("/agb/"))
        self.assertTrue(seo_scan.LEGAL_NOINDEX.search("/datenschutz"))
        self.assertTrue(seo_scan.LEGAL_NOINDEX.search("/imprint"))
        self.assertTrue(seo_scan.LEGAL_NOINDEX.search("/avv"))
        self.assertFalse(seo_scan.LEGAL_NOINDEX.search("/pricing"))
        self.assertNotEqual(seo_scan.netloc_key("https://www.example.com/"), seo_scan.netloc_key("https://example.com/"))

    def test_draft_markers_ignore_product_vocabulary(self) -> None:
        self.assertIsNone(seo_scan.DRAFT_MARKERS.search("Der Entwurfsmodus bleibt auf dem Gerät."))
        self.assertIsNone(seo_scan.DRAFT_MARKERS.search("Status: Entwurf, Live, beendet."))
        self.assertIsNotNone(seo_scan.DRAFT_MARKERS.search("Dieser Abschnitt ist ein Platzhalter und noch in Arbeit."))

    def test_host_alias_without_redirect_is_flagged(self) -> None:
        alias_result = {
            "status": 200,
            "final_url": "https://www.example.com/de/",
            "chain": [],
            "error": None,
        }
        issues = seo_scan.host_alias_issues("https://example.com/de/", lambda url: alias_result)
        self.assertEqual(issues[0]["rule"], "host-alias-200")
        redirected = {
            "status": 200,
            "final_url": "https://example.com/de/",
            "chain": [{"url": "https://www.example.com/de/", "status": 301, "location": "https://example.com/de/"}],
            "error": None,
        }
        self.assertEqual(seo_scan.host_alias_issues("https://example.com/de/", lambda url: redirected), [])

    def test_csr_shell_is_flagged(self) -> None:
        report = self.run_scan()
        rules = {issue["rule"] for issue in report["issues"]}
        self.assertIn("csr-shell", rules)

    def test_soft_404_detection(self) -> None:
        issues = seo_scan.not_found_issues(
            {"status": 200, "error": None}, "https://example.com/"
        )
        self.assertEqual(issues[0]["rule"], "soft-404")
        issues = seo_scan.not_found_issues(
            {"status": 404, "error": None}, "https://example.com/"
        )
        self.assertEqual(issues, [])

    def test_robots_parser(self) -> None:
        robots = seo_scan.Robots("User-agent: *\nDisallow: /private\nAllow: /private/ok\n")
        self.assertFalse(robots.is_allowed("https://example.com/private/x", "test"))
        self.assertTrue(robots.is_allowed("https://example.com/private/ok", "test"))
        self.assertTrue(robots.is_allowed("https://example.com/public", "test"))

    def test_url_normalization_and_skip(self) -> None:
        self.assertEqual(
            seo_scan.normalize_url("HTTPS://Example.com//a/?b=1#c"),
            "https://example.com/a/?b=1",
        )
        self.assertTrue(seo_scan.should_skip("https://example.com/cart"))
        self.assertTrue(seo_scan.should_skip("https://example.com/?s=test"))
        self.assertFalse(seo_scan.should_skip("https://example.com/about"))


if __name__ == "__main__":
    unittest.main()
