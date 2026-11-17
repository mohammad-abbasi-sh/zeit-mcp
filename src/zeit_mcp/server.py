"""MCP server: unofficial read-only access to DIE ZEIT — Germany's
biggest weekly newspaper — via its official RSS feeds at
newsfeed.zeit.de. No key, no login."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import domain as _dom
from . import http as _http

INSTRUCTIONS = """\
Unofficial read-only MCP server for DIE ZEIT — Germany's biggest
weekly newspaper — via its official RSS feeds at newsfeed.zeit.de
(no key, no login). Top headlines, news by section (Politik,
Wirtschaft, Gesellschaft, Digital, Sport, Gesundheit, Arbeit,
Wissenschaft, ZEITmagazin, Hamburg), keyword search across the main
feed or all section feeds, and the list of available sections.
NOTE: www.zeit.de article pages are bot-walled (HTTP 403), so there
is no article-text tool — feeds carry title, link, teaser, author
and publish time, and that is what is returned; nothing is
fabricated.
Built by Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · \
https://mabbasi.ir — Germany MCP factory.\
"""


_SOURCE = "newsfeed.zeit.de"
_DISCLAIMER = "Unofficial read-only data from DIE ZEIT RSS feeds; verify on the site before acting on it."


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


mcp = FastMCP("zeit-mcp", instructions=INSTRUCTIONS)


def _feed(url: str, limit: int) -> dict:
    """Fetch one RSS feed and return its items, newest first, capped."""
    parsed = _dom.parse_rss(_http.fetch_feed(url))
    items = parsed["items"][:limit]
    return {
        "feed_title": parsed["feed_title"],
        "total_results": parsed["count"],
        "count": len(items),
        "items": items,
    }


@mcp.tool()
def zeit_headlines(limit: int = 10) -> str:
    """Top headlines from DIE ZEIT (main RSS feed), newest first.
limit: 1..50 (default 10)."""
    try:
        lim = _dom.validate_limit(limit)
        out = _feed(_dom.HEADLINES_FEED, lim)
    except (_http.ZeitError, ValueError) as e:
        return _err(e)
    return _ok(out)


@mcp.tool()
def zeit_news_by_section(section: str, limit: int = 10) -> str:
    """Newest news of one DIE ZEIT section, in feed order. section:
"politik", "wirtschaft", "gesellschaft", "digital", "sport",
"gesundheit", "arbeit", "wissenschaft", "zeit-magazin" or "hamburg"
(German names work too, e.g. "Wirtschaft"). limit: 1..50
(default 10)."""
    try:
        lim = _dom.validate_limit(limit)
        entry = _dom.normalise_section(section)
        out = _feed(entry["url"], lim)
    except (_http.ZeitError, ValueError) as e:
        return _err(e)
    return _ok({"section": entry["section"], "section_name": entry["name"], **out})


@mcp.tool()
def zeit_search_news(query: str, limit: int = 10) -> str:
    """Search DIE ZEIT news by keyword (title + teaser) in the main
feed. query: free text, e.g. "Bundestag" or "KI". limit: 1..50
(default 10). Searches the main feed (15 items) client-side,
newest first, de-duplicated by link."""
    try:
        if not (query or "").strip():
            return _ok({"error": "query must not be empty"})
        lim = _dom.validate_limit(limit)
        parsed = _dom.parse_rss(_http.fetch_feed(_dom.HEADLINES_FEED))
        found = _dom.dedupe_sort(_dom.search_items(parsed["items"], query.strip()))
        out = {
            "query": query.strip(),
            "total_results": len(found),
            "count": min(lim, len(found)),
            "items": found[:lim],
        }
    except (_http.ZeitError, ValueError) as e:
        return _err(e)
    return _ok(out)


@mcp.tool()
def zeit_search_all_sections(query: str, limit: int = 10) -> str:
    """Search DIE ZEIT news by keyword (title + teaser) across ALL 10
section feeds. query: free text, e.g. "Klimaschutz". limit: 1..50
(default 10). Fetches every section feed, de-duplicates by link,
newest first."""
    try:
        if not (query or "").strip():
            return _ok({"error": "query must not be empty"})
        lim = _dom.validate_limit(limit)
        all_items: list[dict] = []
        for entry in _dom.SECTIONS:
            parsed = _dom.parse_rss(_http.fetch_feed(entry["url"]))
            all_items.extend(parsed["items"])
        found = _dom.dedupe_sort(_dom.search_items(all_items, query.strip()))
        out = {
            "query": query.strip(),
            "total_results": len(found),
            "count": min(lim, len(found)),
            "items": found[:lim],
        }
    except (_http.ZeitError, ValueError) as e:
        return _err(e)
    return _ok(out)


@mcp.tool()
def zeit_sections() -> str:
    """The 10 DIE ZEIT sections with RSS feeds: slug, German name and
feed URL. (kultur, wissen, geschichte and karriere have no RSS feed;
ausland/deutschland/leben redirect to bot-walled pages.)"""
    try:
        sections = _dom.list_sections()
    except ValueError as e:
        return _err(e)
    return _ok({"count": len(sections), "sections": sections})


@mcp.tool()
def zeit_health() -> str:
    """Check whether the DIE ZEIT RSS feeds are reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
