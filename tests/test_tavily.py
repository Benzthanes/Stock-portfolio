import io
import json
import os
import unittest
from unittest.mock import patch, MagicMock

from src.tavily import get_tavily_api_key, search_tavily


class TavilyClientTest(unittest.TestCase):
    def test_get_tavily_api_key_empty_without_env(self):
        """No key is hard-coded: without TAVILY_API_KEY the key is empty and search refuses to run."""
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_tavily_api_key(), "")
            with self.assertRaises(ValueError):
                search_tavily("test query")

    def test_get_tavily_api_key_from_env(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test-12345"}):
            key = get_tavily_api_key()
            self.assertEqual(key, "tvly-test-12345")

    def test_search_tavily_missing_key_raises(self):
        with self.assertRaises(ValueError):
            search_tavily("test query", api_key="")

    @patch("urllib.request.urlopen")
    def test_search_tavily_payload_and_response(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "query": "NVDA earnings",
            "results": [
                {
                    "title": "NVIDIA Q3 Earnings",
                    "url": "https://nvidianews.nvidia.com/news/123",
                    "content": "NVIDIA reported record revenue of $35 billion."
                }
            ]
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = search_tavily("NVDA earnings", api_key="tvly-mock-key", max_results=3)

        self.assertEqual(res["query"], "NVDA earnings")
        self.assertEqual(len(res["results"]), 1)
        self.assertEqual(res["results"][0]["title"], "NVIDIA Q3 Earnings")

        # Verify request call arguments
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.full_url, "https://api.tavily.com/search")
        self.assertEqual(req.headers["Content-type"], "application/json")
        body = json.loads(req.data.decode("utf-8"))
        self.assertEqual(body["api_key"], "tvly-mock-key")
        self.assertEqual(body["query"], "NVDA earnings")
        self.assertEqual(body["max_results"], 3)


if __name__ == "__main__":
    unittest.main()

