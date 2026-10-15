"""
Financial News & Catalyst Engine
Fetches live headlines and market catalysts via RSS for US stocks.
Includes sentiment classification (Bullish vs Bearish), parallel batch fetching, and caching.
"""

import json
import re
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / ".news_cache.json"
CACHE_TTL_SECONDS = 1800  # 30 minutes
_CACHE_LOCK = threading.Lock()

import urllib.parse

TICKER_SEARCH_MAP = {
    "APP": "AppLovin stock OR advertising",
    "BAC": "Bank of America stock OR earnings",
    "NOK": "Nokia stock OR 5G OR Infinera",
    "VRT": "Vertiv stock OR datacenter OR cooling",
    "LLY": "Eli Lilly stock OR Mounjaro",
    "GOOGL": "Alphabet Google stock",
    "ABNB": "Airbnb stock",
    "MNST": "Monster Beverage stock",
    "VOO": "S&P 500 VOO ETF"
}

BEARISH_KEYWORDS = {
    "downgrade", "downgrades", "downgraded", "drop", "drops", "dropped", "fall", "falls",
    "fell", "slide", "slides", "losing", "dispute", "lawsuit", "probe",
    "investigation", "miss", "misses", "missed", "warning", "caution", "weak", "weakness",
    "sell", "debt", "tariff", "antitrust", "slashes", "slashed", "loss", "losses", "delay",
    "delays", "delayed", "tumble", "tumbles", "tumbled", "plunge", "plunges", "plunged",
    "sink", "sinks", "sank", "headwind", "struggle", "struggles", "struggling", "underperform",
    "penalty", "record low", "record lows", "52-week low", "dip", "pullback", "narrow range", "selloff",
    "reject", "rejects", "rejected", "rejection", "declines to approve"
}

BULLISH_KEYWORDS = {
    "upgrade", "upgrades", "upgraded", "record", "beat", "beats", "beating", "soar",
    "soars", "soared", "gain", "gains", "gained", "rise", "rises", "invest", "investment",
    "expansion", "profit", "profits", "profitable", "approval", "approves", "approved", "partner",
    "partnership", "surge", "surges", "surged", "growth", "growing", "dividend", "boost",
    "boosts", "outperform", "opportunity", "moat", "rebound", "rebounds", "bull", "bullish",
    "rally", "rallies", "grew", "cheaper", "edge", "buy", "picks", "picks ahead", "winning streak"
}

_BEAR_REGEX = re.compile(r'\b(' + '|'.join(re.escape(k) for k in BEARISH_KEYWORDS) + r')\b', re.IGNORECASE)
_BULL_REGEX = re.compile(r'\b(' + '|'.join(re.escape(k) for k in BULLISH_KEYWORDS) + r')\b(?!\s+lows?\b)', re.IGNORECASE)
_AI_REGEX = re.compile(r'\b(ai|artificial intelligence)\b', re.IGNORECASE)
_NEUTRAL_PHRASE_REGEX = re.compile(r'\bweight[- ]loss\b', re.IGNORECASE)


def _load_cache() -> Dict[str, Any]:
    if not CACHE_FILE.exists():
        return {}
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        now = time.time()
        return {k: v for k, v in data.items() if (now - v.get("cached_at", 0)) < CACHE_TTL_SECONDS}
    except Exception:
        return {}


def _save_cache(cache: Dict[str, Any]) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _get_from_cache(ticker: str, max_items: int) -> Optional[List[Dict[str, str]]]:
    with _CACHE_LOCK:
        cache = _load_cache()
        entry = cache.get(ticker)
        if entry is None:
            return None
        articles = entry.get("articles", [])
        if entry.get("max_items", len(articles)) < max_items:
            return None
        return articles


def _update_cache(ticker: str, articles: List[Dict[str, str]], max_items: int) -> None:
    with _CACHE_LOCK:
        cache = _load_cache()
        cache[ticker] = {
            "cached_at": time.time(),
            "max_items": max_items,
            "articles": articles
        }
        _save_cache(cache)


def _format_relative_time(pub_date_str: str) -> str:
    """Format RFC 822 date to a clean relative string (e.g., '3h ago', '1d ago')."""
    try:
        dt = parsedate_to_datetime(pub_date_str)
        diff = time.time() - dt.timestamp()
        if diff < 3600:
            mins = max(1, int(diff / 60))
            return f"{mins}m ago"
        elif diff < 86400:
            hrs = int(diff / 3600)
            return f"{hrs}h ago"
        else:
            days = int(diff / 86400)
            return f"{days}d ago"
    except Exception:
        return pub_date_str[:16] if pub_date_str else ""


def classify_sentiment(title: str) -> str:
    """
    Classify a headline as 'bullish', 'bearish', or 'neutral' using whole-word regex matching.
    """
    title = _NEUTRAL_PHRASE_REGEX.sub(" ", title)
    is_bear = bool(_BEAR_REGEX.search(title))
    is_bull = bool(_BULL_REGEX.search(title) or _AI_REGEX.search(title))

    if is_bear and not is_bull:
        return "bearish"
    elif is_bull and not is_bear:
        return "bullish"
    elif is_bear and is_bull:
        return "mixed"
    return "neutral"


def fetch_stock_news(ticker: str, max_items: int = 4, timeout: int = 6) -> List[Dict[str, str]]:
    """
    Fetch the latest market news and catalysts for a specific stock ticker with sentiment tags.
    """
    clean_ticker = ticker.strip().upper()
    cached = _get_from_cache(clean_ticker, max_items)
    if cached is not None:
        return cached[:max_items]

    search_query = TICKER_SEARCH_MAP.get(clean_ticker, f"{clean_ticker} stock")
    encoded_q = urllib.parse.quote(search_query)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-US&gl=US&ceid=US:en"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    req = urllib.request.Request(url, headers=headers)
    articles: List[Dict[str, str]] = []

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
            tree = ET.fromstring(content)
            items = tree.findall(".//item")

            for item in items[:max_items]:
                raw_title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""

                # Extract title and source (format: "Headline - Source Name")
                title = raw_title
                source = "News"
                if " - " in raw_title:
                    parts = raw_title.rsplit(" - ", 1)
                    title = parts[0].strip()
                    source = parts[1].strip()

                title = re.sub(r"<[^>]+>", "", title).strip()
                sentiment = classify_sentiment(title)

                articles.append({
                    "title": title,
                    "source": source,
                    "link": link,
                    "published": _format_relative_time(pub_date),
                    "raw_date": pub_date,
                    "sentiment": sentiment
                })

        _update_cache(clean_ticker, articles, max_items)

    except Exception:
        return []

    return articles[:max_items]


def get_catalyst_breakdown(ticker: str, max_items: int = 4) -> Dict[str, Any]:
    """
    Get news categorized into Bullish Catalysts, Bearish Risks, and All items.
    """
    articles = fetch_stock_news(ticker, max_items=max_items)
    for a in articles:
        if "sentiment" not in a:
            a["sentiment"] = classify_sentiment(a.get("title", ""))

    bullish = [a for a in articles if a["sentiment"] == "bullish"]
    bearish = [a for a in articles if a["sentiment"] == "bearish"]
    neutral_or_mixed = [a for a in articles if a["sentiment"] in ("neutral", "mixed")]

    return {
        "ticker": ticker.upper(),
        "bullish": bullish,
        "bearish": bearish,
        "neutral": neutral_or_mixed,
        "all": articles
    }


def fetch_batch_news(tickers: List[str], max_items: int = 3, max_workers: int = 5) -> Dict[str, List[Dict[str, str]]]:
    """
    Fetch news for multiple tickers in parallel.
    """
    results: Dict[str, List[Dict[str, str]]] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {
            executor.submit(fetch_stock_news, t, max_items): t.upper()
            for t in tickers
        }
        for future in as_completed(future_to_ticker):
            t = future_to_ticker[future]
            try:
                results[t] = future.result()
            except Exception:
                results[t] = []
    return results


def fetch_batch_catalysts(tickers: List[str], max_items: int = 4, max_workers: int = 5) -> Dict[str, Dict[str, Any]]:
    """
    Fetch categorized catalysts (Bullish vs Bearish) for multiple tickers in parallel.
    """
    results: Dict[str, Dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {
            executor.submit(get_catalyst_breakdown, t, max_items): t.upper()
            for t in tickers
        }
        for future in as_completed(future_to_ticker):
            t = future_to_ticker[future]
            try:
                results[t] = future.result()
            except Exception:
                results[t] = {"ticker": t, "bullish": [], "bearish": [], "neutral": [], "all": []}
    return results
