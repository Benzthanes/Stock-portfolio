import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import ai_news, news


class AiNewsIntegrationTest(unittest.TestCase):
    def test_ai_news_cache_save_and_load(self):
        with tempfile.TemporaryDirectory() as d:
            fake_cache_file = Path(d) / "ai_news_cache.json"
            with mock.patch.object(ai_news, "AI_CACHE_FILE", fake_cache_file):
                self.assertEqual(ai_news.load_ai_news_cache(), {})
                sample = {
                    "NOK": {
                        "updated_at": "2026-10-17T17:00:00",
                        "articles": [
                            {
                                "title": "Nokia Q3 update",
                                "title_th": "อัปเดตผลประกอบการ Nokia Q3",
                                "sentiment": "bullish",
                                "summary_th": "สรุปผลประกอบการดี",
                                "ai_analyzed": True
                            }
                        ]
                    }
                }
                ai_news.save_ai_news_cache(sample)
                loaded = ai_news.load_ai_news_cache()
                self.assertIn("NOK", loaded)
                self.assertEqual(len(loaded["NOK"]["articles"]), 1)
                self.assertTrue(loaded["NOK"]["articles"][0]["ai_analyzed"])

    def test_news_enrich_prioritizes_ai_cache(self):
        fake_ai_article = {
            "title": "Nokia signs big 5G deal",
            "title_th": "Nokia คว้าดีล 5G มูลค่ามหาศาล",
            "sentiment": "bullish",
            "summary_th": "วิเคราะห์โดย AI เชิงลึก",
            "impact_th": "บวกต่อรายได้ระยะยาว",
            "action_th": "ทยอยสะสม",
            "topic": "เทคโนโลยีและโทรคมนาคม",
            "ai_analyzed": True
        }
        with mock.patch("src.ai_news.get_ai_analyzed_article", return_value=fake_ai_article):
            articles = [{"title": "Nokia signs big 5G deal", "source": "Reuters", "link": "https://example.com/1"}]
            news._enrich_articles(articles, "NOK")
            self.assertEqual(articles[0]["title_th"], "Nokia คว้าดีล 5G มูลค่ามหาศาล")
            self.assertEqual(articles[0]["summary_th"], "วิเคราะห์โดย AI เชิงลึก")
            self.assertTrue(articles[0]["ai_analyzed"])


if __name__ == "__main__":
    unittest.main()
