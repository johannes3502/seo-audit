from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT if (ROOT / "SKILL.md").exists() else Path(
    os.environ.get("SEO_AUDIT_SKILL", Path.home() / ".kilo" / "skills" / "seo-audit")
)
SCANNER = SKILL_ROOT / "scripts" / "repo_scan.py"

spec = importlib.util.spec_from_file_location("repo_scan", SCANNER)
assert spec and spec.loader
repo_scan = importlib.util.module_from_spec(spec)
sys.modules["repo_scan"] = repo_scan
spec.loader.exec_module(repo_scan)


def write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class RepoScannerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def scan(self, keyword_data=None) -> dict:
        return repo_scan.scan(self.root, 1000, keyword_data)

    def test_next_client_page_and_metadata(self) -> None:
        write(self.root, "package.json", json.dumps({"dependencies": {"next": "15", "react": "19"}}))
        write(self.root, "app/layout.tsx", """
export const metadata = { title: "Home", description: "A generic description." };
export default function Layout({ children }) { return <html lang="de"><body>{children}</body></html>; }
""")
        write(self.root, "app/page.tsx", """
"use client";
import { useEffect } from "react";
export default function Page() {
  useEffect(() => { fetch("/api/content"); }, []);
  return <main><h1>Startseite</h1><img src="/hero.jpg" loading="lazy" /></main>;
}
""")
        write(self.root, "app/about/page.tsx", """
export const metadata = { title: "Über uns", description: "Wer wir sind und was wir tun." };
export default function About() { return <main><h1>Über uns</h1></main>; }
""")
        write(self.root, "app/not-found.tsx", "export default function NotFound() { return <h1>404</h1>; }")
        write(self.root, "app/sitemap.ts", "export default function sitemap() { return []; }")
        write(self.root, "public/robots.txt", "User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n")

        report = self.scan()
        rules = {issue["rule"] for issue in report["issues"]}
        self.assertEqual(report["project"]["framework"], "next-app")
        self.assertIn("client-page", rules)
        self.assertIn("title-generic", rules)
        self.assertIn("image-alt-missing", rules)
        self.assertIn("lcp-image-lazy", rules)
        self.assertIn("title-missing-in-route", rules)
        self.assertGreaterEqual(report["summary"]["routes_detected"], 2)

    def test_vite_spa_is_flagged(self) -> None:
        write(self.root, "package.json", json.dumps({"dependencies": {"vite": "7", "react": "19"}}))
        write(self.root, "vite.config.js", "export default {};")
        write(self.root, "index.html", """
<!doctype html><html><head><title>My App</title></head>
<body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body></html>
""")
        write(self.root, "src/main.tsx", "import './style.css';")
        report = self.scan()
        rules = {issue["rule"] for issue in report["issues"]}
        self.assertEqual(report["project"]["framework"], "vite-spa")
        self.assertEqual(report["project"]["rendering"], "csr")
        self.assertIn("csr-only-app", rules)
        self.assertIn("csr-only-shell", rules)

    def test_vite_router_and_use_meta(self) -> None:
        write(self.root, "package.json", json.dumps({"dependencies": {"vite": "7", "react": "19", "react-router-dom": "7"}}))
        write(self.root, "vite.config.js", "export default {};")
        write(self.root, "index.html", '<div id="root"></div><script type="module" src="/src/main.jsx"></script>')
        write(self.root, "src/App.jsx", """
import Home from './pages/Home';
export default function App() {
  return <Routes><Route path="/" element={<Home />} /></Routes>;
}
""")
        write(self.root, "src/pages/Home.jsx", """
import { useMeta } from '../hooks/useMeta';
export default function Home() {
  useMeta({ title: 'Startseite', description: 'Eine Beschreibung.', canonical: 'https://example.com/' });
  return <main><h1>Startseite</h1></main>;
}
""")
        report = self.scan()
        self.assertEqual(report["project"]["framework"], "vite-spa")
        self.assertEqual(report["routes"][0]["route"], "/")
        self.assertEqual(report["routes"][0]["title"], "Startseite")

    def test_keyword_cannibalization(self) -> None:
        write(self.root, "package.json", json.dumps({"dependencies": {"next": "15", "react": "19"}}))
        write(self.root, "app/page.tsx", "export const metadata = { title: 'Inventory Management Software', description: '...' }; export default function P(){ return <h1>Inventory Management Software</h1>; }")
        write(self.root, "app/inventory/page.tsx", "export const metadata = { title: 'Inventory Management Software', description: '...' }; export default function P(){ return <h1>Inventory Management Software</h1>; }")
        report = self.scan({"pages": [
            {"url": "/", "primary": "inventory management software"},
            {"url": "/inventory", "primary": "inventory management software"},
        ]})
        rules = {issue["rule"] for issue in report["issues"]}
        self.assertIn("keyword-cannibalization", rules)

    def test_global_noindex_and_canonical(self) -> None:
        write(self.root, "package.json", json.dumps({"dependencies": {"next": "15", "react": "19"}}))
        write(self.root, "app/layout.tsx", """
export const metadata = { title: "Site", robots: { index: false }, alternates: { canonical: "https://example.com" } };
export default function Layout({ children }) { return <html><body>{children}</body></html>; }
""")
        report = self.scan()
        rules = {issue["rule"] for issue in report["issues"]}
        self.assertIn("global-noindex", rules)
        self.assertIn("global-canonical", rules)

    def test_next_app_router_in_src_dir_ignores_nested_layouts(self) -> None:
        write(self.root, "package.json", json.dumps({"dependencies": {"next": "16", "react": "19"}}))
        write(self.root, "next.config.ts", "export default { output: 'export' };")
        write(self.root, "src/app/layout.tsx", """
export const metadata = {
  title: { default: "Example", template: "%s | Example" },
  description: "Default description for every route.",
  alternates: { canonical: "/" },
  robots: { index: true, follow: true },
};
export default function Layout({ children }) { return <html lang="de"><body>{children}</body></html>; }
""")
        write(self.root, "src/app/(marketing)/layout.tsx", """
export const metadata = { robots: { index: false, follow: false } };
export default function GroupLayout({ children }) { return <section>{children}</section>; }
""")
        write(self.root, "src/app/(marketing)/page.tsx", """
export const metadata = { title: "Marketing" };
export default function Page() { return <main><h1>Marketing</h1></main>; }
""")
        write(self.root, "src/app/page.tsx", "\"use client\";\nexport default function Page() { return <main><h1>Start</h1></main>; }")
        write(self.root, "src/app/robots.ts", "export default function robots() { return { rules: [{ userAgent: '*', allow: '/' }] }; }")
        write(self.root, "src/app/sitemap.ts", "export default function sitemap() { return []; }")

        report = self.scan({"pages": [{"url": "/", "primary": "example"}]})
        rules = {issue["rule"] for issue in report["issues"]}
        self.assertEqual(report["project"]["framework"], "next-app")
        self.assertGreaterEqual(report["summary"]["routes_detected"], 2)
        self.assertNotIn("global-noindex", rules)
        self.assertNotIn("robots-missing", rules)
        self.assertNotIn("not-found-missing", rules)
        self.assertNotIn("keyword-route-not-found", rules)
        client_pages = [issue for issue in report["issues"] if issue["rule"] == "client-page"]
        self.assertTrue(client_pages)
        self.assertEqual(client_pages[0]["severity"], "info")

    def test_fastapi_is_not_static_and_email_templates_are_not_routes(self) -> None:
        write(self.root, "pyproject.toml", "[project]\ndependencies = [\"fastapi\", \"uvicorn\"]\n")
        write(self.root, "src/api_server/services/email_templates/welcome.html", "<html><body>Hello</body></html>")
        write(self.root, "src/api_server/routers/admin/static/admin.html", "<html><body>Admin</body></html>")

        report = self.scan()
        self.assertEqual(report["project"]["framework"], "fastapi")
        self.assertEqual(report["summary"]["routes_detected"], 0)
        files = {route["file"] for route in report["routes"]}
        self.assertFalse(any("email_templates" in file for file in files))

    def test_astro_dynamic_metadata_and_links_are_not_defects(self) -> None:
        write(self.root, "package.json", json.dumps({"devDependencies": {"astro": "^7"}}))
        write(self.root, "astro.config.mjs", "export default {};")
        write(self.root, "src/pages/index.astro", """
---
import BaseLayout from '../layouts/BaseLayout.astro';
import { meta, links } from '../lib/content';
---
<BaseLayout title={meta.title} description={meta.description}>
  <h1>Start</h1>
  {links.map((link) => <a href={link.href}>{link.label}</a>)}
</BaseLayout>
""")
        report = self.scan()
        self.assertEqual(report["project"]["framework"], "astro")
        rules = {issue["rule"] for issue in report["issues"]}
        self.assertNotIn("link-not-crawlable", rules)
        title_issues = [issue for issue in report["issues"] if issue["rule"] == "title-missing-in-route"]
        self.assertTrue(title_issues)
        self.assertEqual(title_issues[0]["severity"], "info")

    def test_astro_draft_and_bundled_css(self) -> None:
        write(self.root, "package.json", json.dumps({"devDependencies": {"astro": "^7"}}))
        write(self.root, "astro.config.mjs", "export default {};")
        write(self.root, "src/pages/draft.astro", """
---
import BaseLayout from '../layouts/BaseLayout.astro';
---
<BaseLayout title="Draft page" description="A draft page for the test.">
  <h1>Draft</h1>
  <p>Dieser Abschnitt ist ein Platzhalter und noch in Arbeit.</p>
</BaseLayout>
""")
        write(self.root, "src/styles/tokens.css", "@import './colors.css';\n")
        report = self.scan()
        rules = {issue["rule"]: issue for issue in report["issues"]}
        self.assertIn("draft-indexable", rules)
        self.assertEqual(rules["draft-indexable"]["severity"], "low")
        self.assertIn("css-import", rules)
        self.assertEqual(rules["css-import"]["severity"], "info")

    def test_utf16_requirements_detects_fastapi_backend(self) -> None:
        (self.root / "requirements.txt").write_bytes(
            "fastapi==0.136.3\nuvicorn==0.40.0\n".encode("utf-16")
        )
        write(self.root, "app.py", "from fastapi import FastAPI\napp = FastAPI()\n")
        report = self.scan()
        self.assertEqual(report["project"]["framework"], "fastapi")
        self.assertEqual(report["project"]["app_type"], "backend")
        self.assertIsNone(report["summary"]["score"])
        self.assertNotIn("sitemap-missing", {issue["rule"] for issue in report["issues"]})

    def test_umbrella_root_is_inventory_not_site_score(self) -> None:
        write(self.root, ".gitmodules", "[submodule \"frontend\"]\n\tpath = frontend\n\turl = https://example.com/frontend.git\n")
        write(self.root, "frontend/site/package.json", json.dumps({"dependencies": {"vite": "7", "react": "19"}}))
        write(self.root, "frontend/site/vite.config.js", "export default {};")
        write(self.root, "frontend/site/index.html", '<div id="root"></div><script type="module" src="/src/main.jsx"></script>')
        write(self.root, "frontend/site/src/App.jsx", """
import Home from './pages/Home';
export default function App() { return <Routes><Route path="/" element={<Home />} /></Routes>; }
""")
        write(self.root, "frontend/site/src/pages/Home.jsx", "export default function Home(){ return <main><h1>Start</h1></main>; }")
        write(self.root, "docs/TODO.md", "# TODO\n\n- [ ] Launch\n")
        write(self.root, "marketing/notes.md", "# Notes\n")
        write(self.root, "backend/requirements.txt", "fastapi\n")
        write(self.root, "backend/app.py", "from fastapi import FastAPI\napp = FastAPI()\n")

        report = self.scan()
        rules = {issue["rule"] for issue in report["issues"]}
        self.assertEqual(report["project"]["app_type"], "umbrella")
        self.assertIsNone(report["summary"]["score"])
        self.assertEqual(report["summary"]["routes_detected"], 0)
        self.assertIn("scan-scope", rules)
        self.assertNotIn("robots-missing", rules)
        self.assertNotIn("sitemap-missing", rules)
        self.assertNotIn("not-found-missing", rules)
        app_paths = {item["path"] for item in report["project"]["apps"]}
        self.assertIn("frontend/site", app_paths)
        self.assertIn("docs", app_paths)
        self.assertTrue(report["project"]["apps"])

    def test_create_browser_router_and_basename(self) -> None:
        write(self.root, "package.json", json.dumps({"dependencies": {"vite": "7", "react": "19", "react-router-dom": "7"}}))
        write(self.root, "vite.config.js", "export default {};")
        write(self.root, "index.html", '<div id="root"></div><script type="module" src="/src/main.jsx"></script>')
        write(self.root, "src/router.jsx", """
import { createBrowserRouter } from 'react-router-dom';
import App from './App';
import Dashboard from './pages/Dashboard';
import StockPage from './pages/StockPage';
export const router = createBrowserRouter([
  { element: <App />, children: [
    { index: true, element: <Dashboard /> },
    { path: 'bestand', element: <StockPage /> },
  ]},
], { basename: '/lager' });
""")
        write(self.root, "src/pages/Dashboard.jsx", "export default function Dashboard(){ return <h1>Dashboard</h1>; }")
        write(self.root, "src/pages/StockPage.jsx", "export default function StockPage(){ return <h1>Bestand</h1>; }")
        report = self.scan()
        routes = {route["route"] for route in report["routes"]}
        self.assertIn("/lager", routes)
        self.assertIn("/lager/bestand", routes)

    def test_runtime_metadata_and_hero_h1_are_info(self) -> None:
        write(self.root, "package.json", json.dumps({"dependencies": {"vite": "7", "react": "19", "react-router-dom": "7"}}))
        write(self.root, "vite.config.js", "export default {};")
        write(self.root, "index.html", '<div id="root"></div><script type="module" src="/src/main.jsx"></script>')
        write(self.root, "src/App.jsx", """
import Home from './pages/Home';
export default function App() { return <Routes><Route path="/" element={<Home />} /></Routes>; }
""")
        write(self.root, "src/pages/Home.jsx", """
import useMeta from '../hooks/useMeta';
import HeroSection from '../components/HeroSection';
export default function Home() {
  useMeta({ title: t('home.title'), description: t('home.description') });
  return <main><HeroSection title="Willkommen" /></main>;
}
""")
        report = self.scan()
        title_issue = next(issue for issue in report["issues"] if issue["rule"] == "title-missing-in-route")
        description_issue = next(issue for issue in report["issues"] if issue["rule"] == "description-missing-in-route")
        h1_issue = next(issue for issue in report["issues"] if issue["rule"] == "h1-missing-in-route")
        self.assertEqual(title_issue["severity"], "info")
        self.assertEqual(description_issue["severity"], "info")
        self.assertEqual(h1_issue["severity"], "info")

    def test_locale_siblings_and_external_sitemap_context(self) -> None:
        write(self.root, "frontend/site/package.json", json.dumps({"dependencies": {"vite": "7", "react": "19"}}))
        write(self.root, "frontend/site/vite.config.js", "export default {};")
        write(self.root, "frontend/site/index.html", '<div id="root"></div><script type="module" src="/src/main.jsx"></script>')
        write(self.root, "frontend/site/src/App.jsx", """
import Home from './pages/Home';
export default function App() {
  return <Routes>
    <Route path="/de/" element={<Home />} />
    <Route path="/en/" element={<Home />} />
  </Routes>;
}
""")
        write(self.root, "frontend/site/src/pages/Home.jsx", "export default function Home(){ return <main><h1>Start</h1></main>; }")
        write(self.root, "frontend/package.json", json.dumps({"scripts": {"site:build": "vite build && node scripts/generate-sitemap.js"}}))
        write(self.root, "frontend/scripts/generate-sitemap.js", "const alternatesFor = () => [{ hreflang: 'de' }];\n")
        write(self.root, "frontend/scripts/lib/website-routes.js", "export const WEBSITE_ROUTES = [];\n")

        report = repo_scan.scan(self.root / "frontend" / "site", 1000, None)
        routes = {route["route"] for route in report["routes"]}
        self.assertIn("/de/", routes)
        self.assertIn("/en/", routes)
        self.assertNotIn("sitemap-missing", {issue["rule"] for issue in report["issues"]})
        hreflang = [issue for issue in report["issues"] if issue["rule"].startswith("hreflang-")]
        self.assertTrue(hreflang)
        self.assertEqual(hreflang[0]["severity"], "low")

    def test_draft_marker_ignores_product_term(self) -> None:
        write(self.root, "package.json", json.dumps({"dependencies": {"vite": "7", "react": "19"}}))
        write(self.root, "vite.config.js", "export default {};")
        write(self.root, "index.html", '<div id="root"></div><script type="module" src="/src/main.jsx"></script>')
        write(self.root, "src/App.jsx", """
import Home from './pages/Home';
export default function App() { return <Routes><Route path="/" element={<Home />} /></Routes>; }
""")
        write(self.root, "src/pages/Home.jsx", """
export default function Home() {
  return <main><h1>App</h1><p>Der Entwurfsmodus bleibt auf dem Gerät.</p></main>;
}
""")
        report = self.scan()
        self.assertNotIn("draft-indexable", {issue["rule"] for issue in report["issues"]})

    def test_canonical_shared_across_routes(self) -> None:
        write(self.root, "package.json", json.dumps({"dependencies": {"next": "15", "react": "19"}}))
        shared = "https://example.com/"
        write(self.root, "app/page.tsx", f"""
export const metadata = {{ title: "Home", alternates: {{ canonical: "{shared}" }} }};
export default function P() {{ return <h1>Home</h1>; }}
""")
        write(self.root, "app/about/page.tsx", f"""
export const metadata = {{ title: "About", alternates: {{ canonical: "{shared}" }} }};
export default function P() {{ return <h1>About</h1>; }}
""")
        report = self.scan()
        self.assertIn("canonical-shared", {issue["rule"] for issue in report["issues"]})

    def test_sitemap_lastmod_build_time(self) -> None:
        write(self.root, "package.json", json.dumps({"dependencies": {"vite": "7", "react": "19"}}))
        write(self.root, "vite.config.js", "export default {};")
        write(self.root, "index.html", '<div id="root"></div><script type="module" src="/src/main.jsx"></script>')
        write(self.root, "src/App.jsx", "export default function App(){ return <main><h1>Home</h1></main>; }")
        write(self.root, "scripts/generate-sitemap.js", "const urls = [{ loc: '/', lastmod: new Date().toISOString() }];\n")
        report = self.scan()
        self.assertIn("sitemap-lastmod-build-time", {issue["rule"] for issue in report["issues"]})

    def test_robots_disallow_public_route(self) -> None:
        write(self.root, "package.json", json.dumps({"dependencies": {"next": "15", "react": "19"}}))
        write(self.root, "app/layout.tsx", """export const metadata = { title: "Site" };
export default function Layout({ children }) { return <html><body>{children}</body></html>; }""")
        write(self.root, "app/page.tsx", """export const metadata = { title: "Home", description: "Home page." };
export default function P(){ return <h1>Home</h1>; }""")
        write(self.root, "app/rental/page.tsx", """export const metadata = { title: "Rental", description: "Rent equipment." };
export default function P(){ return <h1>Rental</h1>; }""")
        write(self.root, "public/robots.txt", "User-agent: *\nDisallow: /rental\n")
        report = self.scan()
        self.assertIn("robots-blocks-public-route", {issue["rule"] for issue in report["issues"]})

    def test_robots_disallow_noindex(self) -> None:
        write(self.root, "package.json", json.dumps({"dependencies": {"next": "15", "react": "19"}}))
        write(self.root, "app/layout.tsx", """export const metadata = { title: "Site" };
export default function Layout({ children }) { return <html><body>{children}</body></html>; }""")
        write(self.root, "app/preview/page.tsx", """export const metadata = { title: "Preview", robots: { index: false } };
export default function P(){ return <h1>Preview</h1>; }""")
        write(self.root, "public/robots.txt", "User-agent: *\nDisallow: /preview\n")
        report = self.scan()
        self.assertIn("robots-blocks-noindex", {issue["rule"] for issue in report["issues"]})

    def test_client_only_i18n_is_not_hreflang_missing(self) -> None:
        write(self.root, "package.json", json.dumps({"dependencies": {"vite": "7", "react": "19"}}))
        write(self.root, "vite.config.js", "export default {};")
        write(self.root, "index.html", '<div id="root"></div><script type="module" src="/src/main.jsx"></script>')
        write(self.root, "src/App.jsx", "export default function App(){ return <main><h1>Start</h1></main>; }")
        write(self.root, "src/locales/de.json", "{}")
        write(self.root, "src/locales/en.json", "{}")
        report = self.scan()
        rules = {issue["rule"] for issue in report["issues"]}
        self.assertIn("client-only-i18n", rules)
        self.assertNotIn("hreflang-missing", rules)


if __name__ == "__main__":
    unittest.main()
