# zeit-mcp 📰

mcp-name: io.github.mohammad-abbasi-sh/zeit-mcp

Inoffizieller **Read-only**-MCP-Server für **[DIE ZEIT](https://www.zeit.de)** — Deutschlands größte Wochenzeitung — über die offiziellen RSS-Feeds auf [newsfeed.zeit.de](https://newsfeed.zeit.de). Top-Schlagzeilen, Nachrichten nach Ressort (10 Ressorts), Stichwortsuche im Haupt-Feed oder über alle Ressort-Feeds, und die Liste der verfügbaren Ressorts. Kein Schlüssel, kein Login.

> Gebaut von Mohammad Abbasi im Rahmen der „Germany MCP factory" (Sepehr-Modell). Nicht mit DIE ZEIT oder dem Zeitverlag verbunden.

## Für KI-Agenten

Zur MCP-Client-Konfiguration hinzufügen (stdio):

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

Oder lokal starten: `python -m zeit_mcp.server` (benötigt `mcp<2`, `httpx`).

## Tools

| Tool | Beschreibung |
|------|--------------|
| `zeit_headlines` | Top-Schlagzeilen (Haupt-RSS-Feed, 15 Einträge), neueste zuerst — `limit` 1..50 |
| `zeit_news_by_section` | Neueste Nachrichten eines Ressorts — `section`: „politik", „wirtschaft", „gesellschaft", „digital", „sport", „gesundheit", „arbeit", „wissenschaft", „zeit-magazin" oder „hamburg" (deutsche Namen funktionieren auch, z. B. „Wirtschaft"), `limit` 1..50 |
| `zeit_search_news` | Nachrichtensuche nach Stichwort (Titel + Teaser) im Haupt-Feed — `query` (z. B. „Bundestag"), `limit` 1..50 |
| `zeit_search_all_sections` | Nachrichtensuche nach Stichwort über alle 10 Ressort-Feeds, ohne Dubletten, neueste zuerst — `query`, `limit` 1..50 |
| `zeit_sections` | Die 10 Ressorts mit RSS-Feed: Slug, deutscher Name und Feed-URL |
| `zeit_health` | Erreichbarkeitsprüfung (ok / blocked / error) — eine höfliche Anfrage |

Beispielausgabe (`zeit_headlines`, `limit` 2):

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

Hinweise:
- Der Server liest die **offiziellen RSS-Feeds** (Haupt-Feed + 10 Ressort-Feeds, je 15 Einträge, live geprüft am 17.11.2026). Die Suche filtert die abgerufenen Feeds clientseitig (die Website-Suche ist wie die Artikelseiten per Bot-Schutz gesperrt).
- **Kein Artikeltext-Tool — ehrlich:** Die Artikelseiten auf `www.zeit.de` antworten von Rechenzentrums-IPs mit HTTP 403 (Centinel-Bot-Challenge), selbst mit vollständigen Browser-Headern und der `/amp`-Variante (geprüft am 17.11.2026). Die Feeds enthalten Titel, Link, Teaser, Autor und Veröffentlichungszeit — das ist es, was dieser Server liefert, nichts Erfundenes. dpa-Meldungen („News") haben im Feed keinen Teaser (ihr `content:encoded` ist nur ein Vorschaubild), daher ist ihre `description` ehrlich leer.
- Ressorts ohne Feed: kultur, wissen, geschichte und karriere sind 404; ausland, deutschland und leben leiten per 301 auf `www.zeit.de`-Listen-Seiten weiter, die per Bot-Schutz gesperrt sind (403) — sie werden daher nicht angeboten.
- Daten: öffentliche RSS-Feeds der ZEIT — kein Schlüssel, kein Login, nur lesend.

## Entwicklung

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_domain.py` — offline, mit den echten aufgezeichneten Haupt- und Ressort-RSS-Feeds
- `tests/test_live.py` — wenige vorsichtige Live-Anfragen an newsfeed.zeit.de

Tests: 36/36 grün (29 offline + 7 live, 17.11.2026).

## Lizenz

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/)

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
