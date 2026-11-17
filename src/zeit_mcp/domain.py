"""Domain logic: shape zeit.de RSS feeds into compact dicts (stdlib only).

Data source: the official DIE ZEIT RSS feeds at newsfeed.zeit.de
(main feed + one feed per section). No key, no login.

Honest limitation: www.zeit.de article pages are bot-walled from
datacenter IPs (HTTP 403, Centinel challenge — verified 2026-11-17
with full browser headers and the /amp variant), so there is no
article-text tool: the feeds carry title, link, teaser, author and
publish time, and that is what this server returns. Never fabricated.
"""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from datetime import timezone
from email.utils import parsedate_to_datetime

BASE = "https://newsfeed.zeit.de"

# Section feeds — all verified live 2026-11-17 (HTTP 200, 15 items each).
# NOT available as feeds (verified): kultur, wissen, geschichte,
# karriere (404); ausland/deutschland/leben 301-redirect to
# www.zeit.de list pages, which are bot-walled (403).
SECTIONS = [
    {"section": "politik", "name": "Politik",
     "url": f"{BASE}/politik/index"},
    {"section": "wirtschaft", "name": "Wirtschaft",
     "url": f"{BASE}/wirtschaft/index"},
    {"section": "gesellschaft", "name": "Gesellschaft",
     "url": f"{BASE}/gesellschaft/index"},
    {"section": "digital", "name": "Digital",
     "url": f"{BASE}/digital/index"},
    {"section": "sport", "name": "Sport",
     "url": f"{BASE}/sport/index"},
    {"section": "gesundheit", "name": "Gesundheit",
     "url": f"{BASE}/gesundheit/index"},
    {"section": "arbeit", "name": "Arbeit",
     "url": f"{BASE}/arbeit/index"},
    {"section": "wissenschaft", "name": "Wissenschaft",
     "url": f"{BASE}/wissenschaft/index"},
    {"section": "zeit-magazin", "name": "ZEITmagazin",
     "url": f"{BASE}/zeit-magazin/index"},
    {"section": "hamburg", "name": "Hamburg",
     "url": f"{BASE}/hamburg/index"},
]

HEADLINES_FEED = f"{BASE}/index"

_SECTION_BY_KEY = {}
for _s in SECTIONS:
    _SECTION_BY_KEY[_s["section"]] = _s
    _SECTION_BY_KEY[_s["name"].lower()] = _s
_SECTION_BY_KEY["zeitmagazin"] = _SECTION_BY_KEY["zeit-magazin"]
_SECTION_BY_KEY["zeit magazin"] = _SECTION_BY_KEY["zeit-magazin"]

_DC_NS = "{http://purl.org/dc/elements/1.1/}"
_CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"


def validate_limit(limit: int) -> int:
    """Clamp/validate the page size (each feed carries 15 items)."""
    if not 1 <= limit <= 50:
        raise ValueError(f"limit out of range: {limit} (expected 1..50)")
    return limit


def normalise_section(section: str) -> dict:
    """Canonical section entry; accepts slug ("politik") or German name."""
    key = (section or "").strip().lower()
    if not key:
        raise ValueError("section must not be empty")
    entry = _SECTION_BY_KEY.get(key)
    if entry is None:
        raise ValueError(
            f"unknown section: {section!r} "
            f"(expected one of {', '.join(s['section'] for s in SECTIONS)})"
        )
    return entry


def list_sections() -> list[dict]:
    """The 10 available section feeds (slug, German name, feed URL)."""
    return [dict(s) for s in SECTIONS]


def _text(elem, tag: str) -> str:
    child = elem.find(tag)
    if child is None or child.text is None:
        return ""
    return html.unescape(child.text).strip()


def _iso(date_text: str) -> str | None:
    if not date_text:
        return None
    try:
        dt = parsedate_to_datetime(date_text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        return None


_TAG_RE = re.compile(r"<[^>]+>")


def _strip_tags(raw: str) -> str:
    text = _TAG_RE.sub("", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def compact_item(item: ET.Element) -> dict:
    """One RSS <item>, compact: title, link, teaser, author, category,
    publish time.

    The <description> is the teaser; dpa "News" items carry an empty
    description, and content:encoded holds only a thumbnail image, so
    those honestly return an empty description. dc:creator is of the
    form "DIE ZEIT: Ausland - Lisa Röther".
    """
    description = _text(item, "description")
    if not description:
        encoded = item.find(f"{_CONTENT_NS}encoded")
        if encoded is not None and encoded.text:
            description = _strip_tags(encoded.text)
            # The feed renders dpa items' missing teaser as the literal
            # string "None" after the thumbnail image — never surface it.
            if description.casefold() == "none":
                description = ""
    return {
        "title": _text(item, "title"),
        "link": _text(item, "link"),
        "description": description,
        "author": _text(item, f"{_DC_NS}creator"),
        "published": _iso(_text(item, "pubDate")),
        "category": _text(item, "category"),
    }


def parse_rss(xml_text: str) -> dict:
    """Parse a newsfeed.zeit.de RSS feed into {feed_title, count, items}.

    Raises ValueError on malformed XML or a non-RSS document (e.g. a
    404 error page saved as text).
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise ValueError(f"invalid RSS XML: {e}") from e
    channel = root.find("channel")
    if channel is None:
        raise ValueError("unexpected RSS shape: no <channel> element")
    items = [compact_item(it) for it in channel.findall("item")]
    return {
        "feed_title": _text(channel, "title"),
        "count": len(items),
        "items": items,
    }


def search_items(items: list, query: str) -> list:
    """Case-insensitive substring match over title + description."""
    q = (query or "").strip().casefold()
    if not q:
        raise ValueError("query must not be empty")
    return [
        it for it in items
        if q in (it.get("title") or "").casefold()
        or q in (it.get("description") or "").casefold()
    ]


def dedupe_sort(items: list) -> list:
    """De-duplicate by link, newest first (empty publish time sorts last)."""
    seen: set[str] = set()
    unique: list[dict] = []
    for it in items:
        if it["link"] in seen:
            continue
        seen.add(it["link"])
        unique.append(it)
    unique.sort(key=lambda it: it.get("published") or "", reverse=True)
    return unique
