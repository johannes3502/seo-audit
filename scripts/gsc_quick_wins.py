#!/usr/bin/env python3
"""Read-only Google Search Console quick wins (v0.2).

Requires:
    pip install google-api-python-client google-auth-oauthlib

This script never requests write access. It reads Search Analytics only.
URL Inspection, sitemaps and indexing requests are intentionally out of scope.

Examples:
    python gsc_quick_wins.py --property sc-domain:example.com \
        --client-secret client_secret.json --days 90 --out gsc-report

    python gsc_quick_wins.py --property https://example.com/ \
        --service-account service-account.json --days 28
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
TOOL_VERSION = "0.1.0"
DATA_DELAY_DAYS = 3
MAX_ROWS = 25_000


def expected_ctr(position: float) -> float:
    """Rough CTR benchmark by position. Use as a heuristic, not a promise."""
    if position <= 1:
        return 0.30
    if position <= 2:
        return 0.15
    if position <= 3:
        return 0.10
    if position <= 4:
        return 0.07
    if position <= 5:
        return 0.05
    if position <= 6:
        return 0.04
    if position <= 7:
        return 0.03
    if position <= 8:
        return 0.025
    if position <= 9:
        return 0.02
    if position <= 10:
        return 0.015
    if position <= 20:
        return 0.01
    return 0.005


def load_credentials(args: argparse.Namespace):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise SystemExit(
            "Missing Google libraries. Install them with:\n"
            "  pip install google-api-python-client google-auth-oauthlib"
        ) from exc

    if args.service_account:
        return service_account.Credentials.from_service_account_file(
            args.service_account, scopes=SCOPES
        )

    token_path = Path(args.token)
    creds = None
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception:
            creds = None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not Path(args.client_secret).exists():
            raise SystemExit(
                f"OAuth client secret not found: {args.client_secret}\n"
                "Create a Desktop OAuth client in Google Cloud, enable the Search Console API, "
                "and pass the downloaded JSON with --client-secret."
            )
        flow = InstalledAppFlow.from_client_secrets_file(args.client_secret, SCOPES)
        creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def query_rows(service, property_name: str, start: date, end: date) -> list[dict[str, Any]]:
    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": ["query", "page"],
        "rowLimit": MAX_ROWS,
        "dataState": "final",
    }
    try:
        response = service.searchanalytics().query(siteUrl=property_name, body=body).execute()
    except Exception as exc:  # noqa: BLE001 - surface Google's error text
        message = str(exc)
        hint = ""
        if "403" in message:
            hint = (
                "\nHint: 403 usually means the account has no access to this property, "
                "or the property string is wrong. Use the exact value from sites.list "
                "(sc-domain:example.com or https://example.com/)."
            )
        elif "404" in message:
            hint = "\nHint: 404 usually means the property string does not match exactly."
        raise SystemExit(f"Search Console query failed: {message}{hint}") from exc
    return response.get("rows", [])


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    quick_wins: list[dict[str, Any]] = []
    ctr_gaps: list[dict[str, Any]] = []
    pages: dict[str, dict[str, Any]] = {}
    queries: dict[str, dict[str, Any]] = {}
    by_query: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        keys = row.get("keys", [])
        if len(keys) < 2:
            continue
        query, page = keys[0], keys[1]
        clicks = float(row.get("clicks", 0))
        impressions = float(row.get("impressions", 0))
        ctr = float(row.get("ctr", 0))
        position = float(row.get("position", 0))

        item = {
            "query": query,
            "page": page,
            "clicks": round(clicks, 1),
            "impressions": round(impressions, 1),
            "ctr": round(ctr, 4),
            "position": round(position, 1),
        }
        by_query[query].append(item)

        if 4 <= position <= 15 and impressions >= 50:
            quick_wins.append(item)

        benchmark = expected_ctr(position)
        if impressions >= 100 and benchmark > 0 and ctr < benchmark * 0.6:
            ctr_gaps.append(
                {
                    **item,
                    "expected_ctr": round(benchmark, 4),
                    "ctr_gap": round(benchmark - ctr, 4),
                }
            )

        page_item = pages.setdefault(
            page,
            {"page": page, "clicks": 0.0, "impressions": 0.0, "position_weight": 0.0},
        )
        page_item["clicks"] += clicks
        page_item["impressions"] += impressions
        page_item["position_weight"] += position * impressions

        query_item = queries.setdefault(
            query,
            {"query": query, "clicks": 0.0, "impressions": 0.0, "position_weight": 0.0},
        )
        query_item["clicks"] += clicks
        query_item["impressions"] += impressions
        query_item["position_weight"] += position * impressions

    def finish(items: dict[str, dict[str, Any]], key: str) -> list[dict[str, Any]]:
        result = []
        for item in items.values():
            impressions = item["impressions"] or 1
            result.append(
                {
                    key: item[key],
                    "clicks": round(item["clicks"], 1),
                    "impressions": round(item["impressions"], 1),
                    "ctr": round(item["clicks"] / impressions, 4),
                    "position": round(item["position_weight"] / impressions, 1),
                }
            )
        return sorted(result, key=lambda entry: (-entry["impressions"], -entry["clicks"]))[:100]

    quick_wins.sort(key=lambda entry: (-entry["impressions"], entry["position"]))
    ctr_gaps.sort(key=lambda entry: (-entry["ctr_gap"] * entry["impressions"], entry["position"]))

    cannibalization = []
    for query, items in by_query.items():
        candidates = [item for item in items if item["impressions"] >= 10]
        if len(candidates) > 1:
            candidates.sort(key=lambda entry: -entry["impressions"])
            cannibalization.append(
                {
                    "query": query,
                    "pages": candidates[:5],
                    "page_count": len(candidates),
                }
            )
    cannibalization.sort(key=lambda entry: -entry["page_count"])

    return {
        "quick_wins": quick_wins[:50],
        "ctr_gaps": ctr_gaps[:50],
        "cannibalization": cannibalization[:25],
        "top_pages": finish(pages, "page"),
        "top_queries": finish(queries, "query"),
        "total_rows": len(rows),
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        f"# Search Console Quick Wins — {result['property']}",
        "",
        f"Period: `{result['start_date']}` to `{result['end_date']}` · "
        f"Generated: `{result['generated_at']}` · Rows: {result['total_rows']}",
        "",
        "> Read-only data. Search Console rows are limited to 25,000 per request "
        "and 50,000 per day per search type; rare queries are omitted by Google.",
        "",
        "## Quick wins (position 4–15)",
        "",
        "| Query | Page | Clicks | Impressions | CTR | Position |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for item in result["quick_wins"]:
        lines.append(
            f"| {item['query']} | {item['page']} | {item['clicks']} | "
            f"{item['impressions']} | {item['ctr']:.1%} | {item['position']} |"
        )
    lines += [
        "",
        "## CTR gaps",
        "",
        "| Query | Page | CTR | Expected | Gap | Impressions | Position |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for item in result["ctr_gaps"]:
        lines.append(
            f"| {item['query']} | {item['page']} | {item['ctr']:.1%} | "
            f"{item['expected_ctr']:.1%} | {item['ctr_gap']:.1%} | "
            f"{item['impressions']} | {item['position']} |"
        )
    lines += [
        "",
        "## Cannibalization candidates",
        "",
        "| Query | Pages | Top page | Impressions |",
        "|---|---:|---|---:|",
    ]
    for item in result["cannibalization"]:
        top = item["pages"][0]
        lines.append(
            f"| {item['query']} | {item['page_count']} | {top['page']} | {top['impressions']} |"
        )
    lines += [
        "",
        "## Top pages",
        "",
        "| Page | Clicks | Impressions | CTR | Position |",
        "|---|---:|---:|---:|---:|",
    ]
    for item in result["top_pages"]:
        lines.append(
            f"| {item['page']} | {item['clicks']} | {item['impressions']} | "
            f"{item['ctr']:.1%} | {item['position']} |"
        )
    lines += [
        "",
        "## Limits",
        "",
        "- No Page Indexing, Core Web Vitals or Links report via the GSC API.",
        "- URL Inspection is sampled separately and limited to 2,000/day/property.",
        "- Data is typically 2–3 days delayed; the query asks for final data.",
        "- CTR benchmarks are heuristics, not Google thresholds.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only GSC quick wins")
    parser.add_argument("--property", required=True,
                        help="Exact property string, e.g. sc-domain:example.com")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--out", default="gsc-report")
    parser.add_argument("--client-secret", default="client_secret.json")
    parser.add_argument("--token", default="token.json")
    parser.add_argument("--service-account", default="")
    args = parser.parse_args(argv)

    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise SystemExit(
            "Missing google-api-python-client. Install with:\n"
            "  pip install google-api-python-client google-auth-oauthlib"
        ) from exc

    end = date.today() - timedelta(days=DATA_DELAY_DAYS)
    start = end - timedelta(days=max(1, args.days) - 1)
    creds = load_credentials(args)
    service = build("searchconsole", "v1", credentials=creds)
    rows = query_rows(service, args.property, start, end)
    result = {
        "tool": {"name": "gsc-quick-wins", "version": TOOL_VERSION},
        "property": args.property,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "generated_at": date.today().isoformat(),
        **aggregate(rows),
    }

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "gsc.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_markdown(result, out_dir / "gsc.md")
    print(f"{result['total_rows']} rows · {len(result['quick_wins'])} quick wins · "
          f"{len(result['ctr_gaps'])} CTR gaps")
    print(f"Report: {out_dir / 'gsc.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
