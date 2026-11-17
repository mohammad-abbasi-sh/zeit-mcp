# zeit-mcp 📰

mcp-name: io.github.mohammad-abbasi-sh/zeit-mcp

Unofficial **read-only** MCP server for **[DIE ZEIT](https://www.zeit.de)** — Germany's biggest weekly newspaper — via its official RSS feeds at [newsfeed.zeit.de](https://newsfeed.zeit.de). Top headlines, news by section (10 Ressorts), keyword search in the main feed or across all section feeds, and the list of available sections. No key, no login.

> Built by Mohammad Abbasi as part of the "Germany MCP factory" (Sepehr-style pipeline). Not affiliated with DIE ZEIT or Zeitverlag.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "zeit": {
      "command": "uvx",
      "args": ["zeit-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m zeit_mcp.server` (needs `mcp<2`, `httpx`).

## Tools

| Tool | Description |
|------|-------------|
| `zeit_headlines` | Top headlines (main RSS feed, 15 items), newest first — `limit` 1..50 |
| `zeit_news_by_section` | Newest news of one section — `section`: "politik", "wirtschaft", "gesellschaft", "digital", "sport", "gesundheit", "arbeit", "wissenschaft", "zeit-magazin" or "hamburg" (German names work too, e.g. "Wirtschaft"), `limit` 1..50 |
| `zeit_search_news` | Search news by keyword (title + teaser) in the main feed — `query` (e.g. "Bundestag"), `limit` 1..50 |
| `zeit_search_all_sections` | Search news by keyword across all 10 section feeds, de-duplicated, newest first — `query`, `limit` 1..50 |
| `zeit_sections` | The 10 sections with RSS feeds: slug, German name and feed URL |
| `zeit_health` | Reachability probe (ok / blocked / error) — one polite request |

Example output (`zeit_headlines`, `limit` 2):

```json
{"feed_title": "DIE ZEIT | Nachrichten, News, Hintergründe und Debatten", "total_results": 15, "count": 2,
 "items": [
  {"title": "Preiserhöhungen: Bus und Bahn: Landestarif im Südwesten wird teurer",
   "link": "https://www.zeit.de/news/2026-11/17/bus-und-bahn-landestarif-im-suedwesten-wird-teurer",
   "description": "", "author": "DIE ZEIT: News -",
   "published": "2026-11-17T10:12:02+00:00", "category": "News"},
  {"title": "Konjunktur: EU-Kommission verdoppelt Wachstumsprognose für Deutschland",
   "link": "https://www.zeit.de/news/2026-11/17/eu-kommission-verdoppelt-wachstumsprognose-fuer-deutschland",
   "description": "", "author": "DIE ZEIT: News -",
   "published": "2026-11-17T10:11:17+00:00", "category": "News"},
  ...]}
```

Notes:
- The server reads the **official RSS feeds** (main feed + 10 section feeds, 15 items each, verified live 2026-11-17). Search filters the fetched feeds client-side (the site search page is bot-walled, like the article pages).
- **No article-text tool — honestly:** `www.zeit.de` article pages answer HTTP 403 (Centinel bot challenge) from datacenter IPs, even with full browser headers and the `/amp` variant (verified 2026-11-17). The feeds carry title, link, teaser, author and publish time — that is what this server returns, nothing fabricated. dpa "News" items carry no teaser in the feed (their `content:encoded` is only a thumbnail), so their `description` is honestly empty.
- Sections without a feed: kultur, wissen, geschichte and karriere are 404; ausland, deutschland and leben 301-redirect to `www.zeit.de` list pages, which are bot-walled (403) — so they are not offered.
- Data: DIE ZEIT public RSS feeds — no key, no login, read-only.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_domain.py` — offline, parses the real captured main + section RSS feeds
- `tests/test_live.py` — cautious live requests against newsfeed.zeit.de

Tests: 36/36 green (29 offline + 7 live, 2026-11-17).

## License

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
