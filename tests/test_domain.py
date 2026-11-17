"""Offline tests — parse the real captured newsfeed.zeit.de RSS feeds
(main + 3 section feeds), no network."""
import json
import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from zeit_mcp import domain as dom
from zeit_mcp import server as srv

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


def _rss(name):
    return dom.parse_rss((FIX / name).read_text(encoding="utf-8"))


class TestHeadlinesFixture(unittest.TestCase):
    def test_headlines_shape(self):
        out = _rss("headlines.xml")
        self.assertEqual(out["feed_title"], "DIE ZEIT | Nachrichten, News, Hintergründe und Debatten")
        self.assertEqual(out["count"], 15)
        self.assertEqual(len(out["items"]), 15)

    def test_headlines_first_item(self):
        item = _rss("headlines.xml")["items"][0]
        self.assertEqual(
            item["title"],
            "Preiserhöhungen: Bus und Bahn: Landestarif im Südwesten wird teurer",
        )
        self.assertEqual(
            item["link"],
            "https://www.zeit.de/news/2026-11/17/bus-und-bahn-landestarif-im-suedwesten-wird-teurer",
        )
        self.assertEqual(item["published"], "2026-11-17T10:12:02+00:00")
        self.assertEqual(item["category"], "News")
        self.assertEqual(item["author"], "DIE ZEIT: News -")

    def test_headlines_all_items_complete(self):
        items = _rss("headlines.xml")["items"]
        self.assertTrue(all(i["title"] and i["link"] and i["published"] for i in items))
        self.assertTrue(all(i["link"].startswith("https://www.zeit.de/") for i in items))

    def test_dpa_items_have_empty_description_not_none(self):
        # dpa "News" items carry an empty <description> and a
        # content:encoded of "<img> None" — the literal "None" must
        # never leak into output.
        items = _rss("headlines.xml")["items"]
        news = [i for i in items if i["category"] == "News"]
        self.assertGreater(len(news), 0)
        # Most dpa News items have no teaser at all in the feed.
        self.assertGreaterEqual(
            sum(1 for i in news if i["description"] == ""), 5)
        self.assertTrue(all(i["description"] != "None" for i in items))

    def test_editorial_items_have_teaser(self):
        item = _rss("headlines.xml")["items"][2]
        self.assertTrue(item["description"].startswith("In der Türkei ist mit Sözcü TV"))
        self.assertEqual(item["author"], "DIE ZEIT: Ausland - Lisa Röther")


class TestSectionFixtures(unittest.TestCase):
    def test_section_politik(self):
        out = _rss("section-politik.xml")
        self.assertEqual(out["feed_title"], "Politik - aktuelle Nachrichten und Reportagen")
        self.assertEqual(out["count"], 15)
        self.assertEqual(
            out["items"][0]["title"],
            "Sözcü TV: Türkische Polizei stürmt oppositionsnahen Sender Sözcü TV",
        )
        self.assertTrue(all(i["link"].startswith("https://www.zeit.de/") for i in out["items"]))

    def test_section_wirtschaft(self):
        out = _rss("section-wirtschaft.xml")
        self.assertEqual(out["feed_title"], "Wirtschaft - Neuigkeiten von der Börse und aus Unternehmen")
        self.assertEqual(out["count"], 15)

    def test_section_zeit_magazin(self):
        out = _rss("section-zeit-magazin.xml")
        self.assertEqual(out["feed_title"], "ZEITmagazin")
        self.assertEqual(out["count"], 15)


class TestParseErrors(unittest.TestCase):
    def test_malformed_xml(self):
        with self.assertRaises(ValueError):
            dom.parse_rss("<rss><channel><item>oops")

    def test_non_rss_document(self):
        with self.assertRaises(ValueError):
            dom.parse_rss("<html><head><title>404</title></head></html>")

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            dom.parse_rss("")


class TestValidation(unittest.TestCase):
    def test_limit_bounds(self):
        self.assertEqual(dom.validate_limit(1), 1)
        self.assertEqual(dom.validate_limit(50), 50)
        with self.assertRaises(ValueError):
            dom.validate_limit(0)
        with self.assertRaises(ValueError):
            dom.validate_limit(51)

    def test_normalise_section(self):
        self.assertEqual(dom.normalise_section("politik")["section"], "politik")
        self.assertEqual(dom.normalise_section("Politik")["name"], "Politik")
        self.assertEqual(dom.normalise_section("wirtschaft")["section"], "wirtschaft")
        self.assertEqual(dom.normalise_section("Wirtschaft")["section"], "wirtschaft")
        self.assertEqual(dom.normalise_section("zeit-magazin")["section"], "zeit-magazin")
        self.assertEqual(dom.normalise_section("ZEITmagazin")["section"], "zeit-magazin")
        self.assertEqual(dom.normalise_section("zeit magazin")["section"], "zeit-magazin")
        with self.assertRaises(ValueError):
            dom.normalise_section("kultur")
        with self.assertRaises(ValueError):
            dom.normalise_section("ausland")
        with self.assertRaises(ValueError):
            dom.normalise_section("")

    def test_sections_all_have_urls(self):
        self.assertEqual(len(dom.SECTIONS), 10)
        for s in dom.SECTIONS:
            self.assertTrue(s["url"].startswith("https://newsfeed.zeit.de/"))

    def test_list_sections(self):
        sections = dom.list_sections()
        self.assertEqual(len(sections), 10)
        self.assertEqual(sections[0]["section"], "politik")
        self.assertEqual(sections[-1]["section"], "hamburg")


class TestSearch(unittest.TestCase):
    def test_search_case_insensitive(self):
        items = _rss("headlines.xml")["items"]
        self.assertEqual(len(dom.search_items(items, "Bus")), 1)
        self.assertEqual(len(dom.search_items(items, "bus")), 1)

    def test_search_counts(self):
        items = _rss("headlines.xml")["items"]
        self.assertEqual(len(dom.search_items(items, "EU")), 8)

    def test_search_no_hits(self):
        items = _rss("headlines.xml")["items"]
        self.assertEqual(dom.search_items(items, "zzzzqqq"), [])

    def test_search_empty_raises(self):
        with self.assertRaises(ValueError):
            dom.search_items([], "  ")

    def test_dedupe_sort(self):
        head = _rss("headlines.xml")["items"]
        pol = _rss("section-politik.xml")["items"]
        merged = dom.dedupe_sort(head + pol)
        links = [i["link"] for i in merged]
        self.assertEqual(len(links), len(set(links)))
        self.assertEqual(len(merged), 27)  # 15 + 15 − 3 shared
        dates = [i["published"] for i in merged]
        self.assertEqual(dates, sorted(dates, reverse=True))


class TestServerOffline(unittest.TestCase):
    """Tool functions with the HTTP layer mocked to the fixtures."""

    def test_headlines_tool(self):
        xml = (FIX / "headlines.xml").read_text(encoding="utf-8")
        with mock.patch.object(srv._http, "fetch_feed", return_value=xml):
            out = json.loads(srv.zeit_headlines(limit=3))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 3)
        self.assertEqual(out["total_results"], 15)
        self.assertEqual(out["source"], "newsfeed.zeit.de")
        self.assertIn("fetched_at", out)

    def test_headlines_tool_limit_error(self):
        out = json.loads(srv.zeit_headlines(limit=0))
        self.assertIn("error", out)

    def test_section_tool(self):
        xml = (FIX / "section-politik.xml").read_text(encoding="utf-8")
        with mock.patch.object(srv._http, "fetch_feed", return_value=xml):
            out = json.loads(srv.zeit_news_by_section("politik", limit=2))
        self.assertNotIn("error", out)
        self.assertEqual(out["section"], "politik")
        self.assertEqual(out["section_name"], "Politik")
        self.assertEqual(out["count"], 2)
        self.assertEqual(out["total_results"], 15)

    def test_section_tool_unknown(self):
        out = json.loads(srv.zeit_news_by_section("kultur", limit=2))
        self.assertIn("error", out)
        self.assertIn("unknown section", out["error"])

    def test_search_tool(self):
        xml = (FIX / "headlines.xml").read_text(encoding="utf-8")
        with mock.patch.object(srv._http, "fetch_feed", return_value=xml):
            out = json.loads(srv.zeit_search_news("Bus", limit=10))
        self.assertNotIn("error", out)
        self.assertEqual(out["query"], "Bus")
        self.assertEqual(out["total_results"], 1)
        self.assertEqual(out["count"], 1)

    def test_search_tool_empty_query(self):
        out = json.loads(srv.zeit_search_news("   "))
        self.assertIn("error", out)

    def test_search_all_sections_tool(self):
        feeds = {
            "https://newsfeed.zeit.de/index": (FIX / "headlines.xml").read_text(encoding="utf-8"),
            "https://newsfeed.zeit.de/politik/index": (FIX / "section-politik.xml").read_text(encoding="utf-8"),
            "https://newsfeed.zeit.de/wirtschaft/index": (FIX / "section-wirtschaft.xml").read_text(encoding="utf-8"),
            "https://newsfeed.zeit.de/zeit-magazin/index": (FIX / "section-zeit-magazin.xml").read_text(encoding="utf-8"),
        }

        def _fake(url):
            return feeds.get(url, (FIX / "headlines.xml").read_text(encoding="utf-8"))

        with mock.patch.object(srv._http, "fetch_feed", side_effect=_fake):
            out = json.loads(srv.zeit_search_all_sections("Sözcü", limit=10))
        self.assertNotIn("error", out)
        self.assertEqual(out["query"], "Sözcü")
        self.assertGreaterEqual(out["total_results"], 1)
        self.assertTrue(all("sözcü" in (i["title"] + i["description"]).casefold() for i in out["items"]))

    def test_sections_tool(self):
        out = json.loads(srv.zeit_sections())
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 10)
        self.assertEqual(out["sections"][0]["section"], "politik")
        self.assertTrue(all(s["url"].startswith("https://newsfeed.zeit.de/") for s in out["sections"]))

    def test_health_tool(self):
        with mock.patch.object(srv._http, "health_check", return_value={"status": "ok", "http_status": 200, "url": dom.HEADLINES_FEED}):
            out = json.loads(srv.zeit_health())
        self.assertEqual(out["status"], "ok")


if __name__ == "__main__":
    unittest.main()
