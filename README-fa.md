# zeit-mcp 📰

mcp-name: io.github.mohammad-abbasi-sh/zeit-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **[DIE ZEIT](https://www.zeit.de)** — بزرگ‌ترین روزنامهٔ هفتگی آلمان — از طریق فیدهای رسمی RSS در [newsfeed.zeit.de](https://newsfeed.zeit.de). تیترهای برتر، اخبار ۱۰ بخش، جست‌وجوی کلیدواژه در فید اصلی یا در همهٔ فیدهای بخش‌ها، و فهرست بخش‌های موجود. بدون کلید، بدون ورود.

> ساختهٔ محمد عباسی در چارچوب «کارخانهٔ MCP آلمان» (مدل سپهر). وابسته به DIE ZEIT یا انتشارات تسایت نیست.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی MCP Client اضافه کنید (stdio):

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

یا اجرای محلی: `python -m zeit_mcp.server` (نیازمند `mcp<2` و `httpx`).

## ابزارها

| ابزار | توضیح |
|------|-------|
| `zeit_headlines` | تیترهای برتر (فید اصلی RSS، ۱۵ مورد)، جدیدترین اول — `limit` بین ۱ تا ۵۰ |
| `zeit_news_by_section` | جدیدترین اخبار یک بخش — `section`: ‏«politik»، «wirtschaft»، «gesellschaft»، «digital»، «sport»، «gesundheit»، «arbeit»، «wissenschaft»، «zeit-magazin» یا «hamburg» (نام آلمانی هم کار می‌کند، مثلاً «Wirtschaft»)، `limit` بین ۱ تا ۵۰ |
| `zeit_search_news` | جست‌وجوی اخبار با کلیدواژه (عنوان + تیزر) در فید اصلی — `query` (مثلاً «Bundestag»)، `limit` بین ۱ تا ۵۰ |
| `zeit_search_all_sections` | جست‌وجوی اخبار با کلیدواژه در همهٔ ۱۰ فید بخش‌ها، بدون تکرار، جدیدترین اول — `query`، `limit` بین ۱ تا ۵۰ |
| `zeit_sections` | ۱۰ بخش دارای فید RSS: اسلاگ، نام آلمانی و آدرس فید |
| `zeit_health` | بررسی در دسترس بودن سایت (ok / blocked / error) — یک درخواست مؤدبانه |

نمونهٔ خروجی (`zeit_headlines` با `limit` برابر ۲):

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

نکته‌ها:
- سرور **فیدهای رسمی RSS** را می‌خواند (فید اصلی + ۱۰ فید بخش‌ها، هر کدام ۱۵ مورد، بررسی زنده در ۱۷ نوامبر ۲۰۲۶). جست‌وجو فیدهای واکشی‌شده را سمت کلاینت فیلتر می‌کند (جست‌وجوی سایت مثل صفحه‌های مقاله با دیوار ربات مسدود است).
- **ابزار متن مقاله ندارد — صادقانه:** صفحه‌های مقالهٔ `www.zeit.de` از آی‌پی‌های دیتاسنتر پاسخ HTTP 403 می‌دهند (چالش ربات Centinel)، حتی با هدرهای کامل مرورگر و نسخهٔ `/amp` (بررسی‌شده در ۱۷ نوامبر ۲۰۲۶). فیدها عنوان، لینک، تیزر، نویسنده و زمان انتشار را دارند — همین چیزی است که این سرور برمی‌گرداند، بدون هیچ متن ساختگی. خبرهای dpa (دستهٔ «News») در فید تیزر ندارند (`content:encoded` آن‌ها فقط یک تصویر بندانگشتی است)، پس `description` آن‌ها صادقانه خالی است.
- بخش‌های بدون فید: kultur و wissen و geschichte و karriere پاسخ ۴۰۴ می‌دهند؛ ausland و deutschland و leben با ۳۰۱ به صفحه‌های فهرست `www.zeit.de` هدایت می‌شوند که با دیوار ربات مسدودند (۴۰۳) — پس ارائه نمی‌شوند.
- داده‌ها: فیدهای عمومی RSS روزنامهٔ تسایت — بدون کلید، بدون ورود، فقط خواندنی.

## توسعه

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_domain.py` — آفلاین، با فیدهای RSS واقعی ضبط‌شدهٔ اصلی و بخش‌ها
- `tests/test_live.py` — چند درخواست زندهٔ محتاطانه به newsfeed.zeit.de

تست‌ها: ۳۶ از ۳۶ سبز (۲۹ آفلاین + ۷ زنده، ۱۷ نوامبر ۲۰۲۶).

## مجوز

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/)

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
