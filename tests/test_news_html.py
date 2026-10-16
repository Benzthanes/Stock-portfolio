import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from src import news
from src.html_report import _make_chart_onclick, _news_items_html
from src.outlook import get_forward_outlook


class SentimentTest(unittest.TestCase):
    def test_labels(self):
        cases = {
            "Eli Lilly weight loss drug sales jump": "neutral",
            "Nvidia extends winning streak": "bullish",
            "FDA rejects Novo drug application": "bearish",
            "FDA declines to approve new therapy": "bearish",
            "FDA approves Lilly Alzheimer's drug": "bullish",
            "Nokia shares hit record low": "bearish",
            "Vertiv posts record revenue": "bullish",
            "Stock slides on losing streak": "bearish",
            "CEO said the company will expand hiring": "neutral",
            "Executive shake-up at Bank of America": "neutral",
            "Company maintains guidance again": "neutral",
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(news.classify_sentiment(title), expected)


class NewsCacheTest(unittest.TestCase):
    def _rss(self, n):
        items = "".join(
            f"<item><title>Headline {i} - Src</title><link>https://ex.com/{i}</link><pubDate></pubDate></item>"
            for i in range(n)
        )
        return f"<rss><channel>{items}</channel></rss>".encode()

    def test_larger_request_not_served_from_smaller_cache(self):
        with tempfile.TemporaryDirectory() as d:
            resp = mock.MagicMock()
            resp.__enter__.return_value.read.return_value = self._rss(6)
            with mock.patch.object(news, "CACHE_FILE", Path(d) / "cache.json"), \
                    mock.patch.object(news, "translate_texts_to_thai", side_effect=lambda ts: list(ts)), \
                    mock.patch("src.http.urllib.request.urlopen", return_value=resp) as urlopen:
                self.assertEqual(len(news.fetch_stock_news("ZZZ", max_items=2)), 2)
                self.assertEqual(len(news.fetch_stock_news("ZZZ", max_items=4)), 4)
                self.assertEqual(len(news.fetch_stock_news("ZZZ", max_items=3)), 3)
                self.assertEqual(urlopen.call_count, 2)
                cached = json.loads((Path(d) / "cache.json").read_text())
                self.assertEqual(cached["ZZZ"]["max_items"], 4)


class NewsHtmlTest(unittest.TestCase):
    def test_title_and_link_escaped(self):
        out = _news_items_html([{
            "title": "<img src=x onerror=alert(1)>",
            "source": "<b>Src</b>",
            "link": "javascript:alert(1)",
            "published": "1h ago",
        }], "empty")
        self.assertEqual(
            out,
            "<li><strong class='source-tag'>[&lt;b&gt;Src&lt;/b&gt;]</strong> "
            "&lt;img src=x onerror=alert(1)&gt; <span class='text-muted small'>(1h ago)</span></li>",
        )

    def test_http_link_quoted(self):
        out = _news_items_html([{"title": "A 'q' & b", "source": "S", "link": "https://ex.com/a'b"}], "empty")
        self.assertIn("href='https://ex.com/a&#x27;b'", out)
        self.assertIn(">A &#x27;q&#x27; &amp; b ↗</a>", out)

    def test_empty(self):
        self.assertEqual(_news_items_html([], "none"), "<li><span class='text-muted'>none</span></li>")

    def test_onclick_safe_in_double_quoted_attribute(self):
        js = _make_chart_onclick({"ticker": "X", "name": 'A "B" O\'Neil <i>', "sector": "Tech", "close_price": 1.5})
        self.assertNotIn('"', js)
        self.assertNotIn("<", js)
        self.assertEqual(
            js,
            "openChartModal(&quot;X&quot;, &quot;NASDAQ&quot;, &quot;A \\&quot;B\\&quot; O&#x27;Neil &lt;i&gt;&quot;, "
            "&quot;Tech&quot;, 0.0, 1.5, 0.0, 0.0, 0.0, 0.0, 0.0)",
        )


class OutlookTest(unittest.TestCase):
    def _all_text(self, ticker, days):
        o = get_forward_outlook(
            ticker,
            {"close": 100.0, "price_target_average": 93.3, "price_target_low": 80.0, "RSI": 55.0},
            {"net_inc_growth_yoy": -5.0, "rev_growth_yoy": 3.0},
            days_to_earnings=days,
            avg_cost=110.0,
            close=100.0,
        )
        return json.dumps(o, ensure_ascii=False)

    def test_no_stale_snapshot_numbers(self):
        for t in ("VRT", "NOK", "BAC", "APP"):
            with self.subTest(ticker=t):
                txt = self._all_text(t, 60)
                for stale in ("13.8", "7.6 วัน", "209.26", "8.90", "RSI 19", "92 วัน", "21 วัน"):
                    self.assertNotIn(stale, txt)
                self.assertIn("60 วัน", txt)

    def test_no_plus_minus(self):
        for t in ("NVDA", "TSLA", "MSFT", "AAPL", "AMZN", "APP", "VRT", "BAC", "NOK", "ZZZ"):
            with self.subTest(ticker=t):
                txt = self._all_text(t, 60)
                self.assertNotIn("+-", txt)
                self.assertIn("-6.7%", txt)

    def test_earnings_freeze_only_when_near(self):
        self.assertIn("5.0 วัน", get_forward_outlook("VRT", {}, {}, 5.0)["tailored_roadmap"])
        self.assertNotIn("ห้ามถัว", get_forward_outlook("VRT", {}, {}, 60)["tailored_roadmap"])
        self.assertNotIn("วัน", get_forward_outlook("NOK", {}, {}, None)["catalyst_timeline"][0]["period"])


class LowerKeywordTest(unittest.TestCase):
    def test_price_cut_and_rate_cut_are_not_bearish(self):
        self.assertEqual(news.classify_sentiment("Apple to lower iPhone prices in China"), "neutral")
        self.assertEqual(news.classify_sentiment("Fed expected to lower rates, stocks rally"), "bullish")

    def test_shares_lower_is_bearish(self):
        self.assertEqual(news.classify_sentiment("Tesla shares lower after delivery report"), "bearish")


class TopicTest(unittest.TestCase):
    def test_substrings_do_not_trigger_topics(self):
        default_topic = "ผลการดำเนินงานและทิศทางธุรกิจ"
        self.assertEqual(news.classify_topic("Analysts said retail demand steady")[0], "มุมมองและอันดับความน่าเชื่อถือจากนักวิเคราะห์ Wall Street")
        self.assertEqual(news.classify_topic("CEO said retail sector demand holds")[0], default_topic)
        self.assertEqual(news.classify_topic("Fundamental shift in second half")[0], default_topic)

    def test_whole_word_ai_topic(self):
        self.assertEqual(news.classify_topic("Microsoft expands AI datacenter push")[0], "เทคโนโลยี AI และการขยายโครงสร้างพื้นฐานดาต้าเซ็นเตอร์")


class TranslateBatchTest(unittest.TestCase):
    def test_falls_back_to_originals_on_network_error(self):
        with mock.patch("src.http.urllib.request.urlopen", side_effect=urllib.error.URLError("blocked")) as urlopen, \
                mock.patch("src.http._sleep"):
            self.assertEqual(news.translate_texts_to_thai(["A", "B", "C"]), ["A", "B", "C"])
            self.assertEqual(urlopen.call_count, 2)

    def test_cache_backfill_is_persisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_file = Path(tmp) / "news_cache.json"
            import time as _time
            cached_at = _time.time() - 60
            cache_file.write_text(json.dumps({"AAA": {"cached_at": cached_at, "max_items": 4, "articles": [
                {"title": "Old headline", "source": "X", "sentiment": "neutral"}
            ]}}), encoding="utf-8")
            with mock.patch.object(news, "CACHE_FILE", cache_file), \
                    mock.patch.object(news, "translate_texts_to_thai", side_effect=lambda ts: ["หัวข้อเก่า" for _ in ts]):
                articles = news.fetch_stock_news("AAA", max_items=4)
            saved = json.loads(cache_file.read_text(encoding="utf-8"))["AAA"]
            self.assertEqual(articles[0]["title_th"], "หัวข้อเก่า")
            self.assertEqual(saved["articles"][0]["title_th"], "หัวข้อเก่า")
            self.assertEqual(saved["cached_at"], cached_at)


if __name__ == "__main__":
    unittest.main()
