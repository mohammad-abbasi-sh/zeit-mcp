"""Live tests — hit the real newsfeed.zeit.de RSS feeds.
Cautious: few requests.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set ZEIT_SKIP_LIVE=1)
"""
import json
import os
import pathlib
import sys
import unittest

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from zeit_mcp import server as srv

pytestmark = pytest.mark.live
SKIP = os.environ.get("ZEIT_SKIP_LIVE") == "1"


@pytest.mark.skipif(SKIP, reason="ZEIT_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_headlines_live(self):
        out = json.loads(srv.zeit_headlines(limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(all(i["title"] and i["link"] for i in out["items"]))
        print(f"\nLIVE headlines: {out['count']} items, first: {out['items'][0]['title']}")

    def test_section_live(self):
        out = json.loads(srv.zeit_news_by_section("politik", limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        print(f"\nLIVE politik: {out['items'][0]['title']}")

    def test_all_sections_live(self):
        # Every section feed must answer with at least one item.
        from zeit_mcp import domain as dom
        for s in dom.SECTIONS:
            out = json.loads(srv.zeit_news_by_section(s["section"], limit=1))
            self.assertNotIn("error", out, f"section {s['section']}")
            self.assertGreaterEqual(out["count"], 1, f"section {s['section']}")
        print(f"\nLIVE all {len(dom.SECTIONS)} sections OK")

    def test_search_live(self):
        out = json.loads(srv.zeit_search_news("Deutschland", limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(all(
            "deutschland" in (i["title"] + i["description"]).casefold()
            for i in out["items"]
        ))
        print(f"\nLIVE search 'Deutschland': {out['total_results']} hits")

    def test_search_all_sections_live(self):
        out = json.loads(srv.zeit_search_all_sections("Deutschland", limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(all(
            "deutschland" in (i["title"] + i["description"]).casefold()
            for i in out["items"]
        ))
        print(f"\nLIVE search-all 'Deutschland': {out['total_results']} hits")

    def test_sections_live(self):
        out = json.loads(srv.zeit_sections())
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 10)

    def test_health_live(self):
        out = json.loads(srv.zeit_health())
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["http_status"], 200)
