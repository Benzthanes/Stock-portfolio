"""
AI News Intelligence Manager.
Manages AI-driven news translation, contextual market impact analysis, and strategy synthesis.
Prioritizes high-quality AI analysis generated in AGY and maintains fallback for automated workflows.
"""

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
AI_CACHE_FILE = DATA_DIR / "ai_news_cache.json"
PROGRAMMATIC_CACHE_FILE = DATA_DIR / ".news_cache.json"


def load_ai_news_cache() -> Dict[str, Any]:
    """Loads the human/AI curated news analysis cache."""
    if not AI_CACHE_FILE.exists():
        return {}
    try:
        with open(AI_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ai_news] Failed to read {AI_CACHE_FILE}: {e}", file=sys.stderr)
        return {}


def save_ai_news_cache(cache: Dict[str, Any]) -> None:
    """Saves AI news cache atomically."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=DATA_DIR, prefix="ai_news_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        os.replace(tmp, AI_CACHE_FILE)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def get_ai_analyzed_article(ticker: str, title: str, link: str = "") -> Optional[Dict[str, Any]]:
    """
    Checks if an article has an existing high-quality AI analysis in ai_news_cache.json.
    Matches either by exact link or normalized title.
    """
    ai_cache = load_ai_news_cache()
    t_data = ai_cache.get(ticker.upper(), {})
    articles = t_data.get("articles", [])

    norm_title = title.strip().lower()
    norm_link = link.strip().lower() if link else ""

    for a in articles:
        a_title = (a.get("title") or "").strip().lower()
        a_link = (a.get("link") or "").strip().lower()
        if (norm_link and a_link and norm_link == a_link) or (norm_title and a_title and norm_title == a_title):
            return a
    return None


def merge_ai_articles(ticker: str, articles: List[Dict[str, Any]]) -> None:
    """
    Merges newly analyzed articles into ai_news_cache.json for a ticker.
    Tags each with ai_analyzed=True and timestamp.
    """
    ai_cache = load_ai_news_cache()
    t_up = ticker.upper().strip()
    existing_entry = ai_cache.get(t_up, {"updated_at": "", "articles": []})
    existing_articles = existing_entry.get("articles", [])

    # Index by link and title
    merged = []
    seen = set()

    for new_a in articles:
        key = (new_a.get("link") or new_a.get("title") or "").strip()
        if not key or key in seen:
            continue
        new_a["ai_analyzed"] = True
        new_a["ai_analyzed_at"] = new_a.get("ai_analyzed_at") or datetime.now().isoformat()
        merged.append(new_a)
        seen.add(key)

    for old_a in existing_articles:
        key = (old_a.get("link") or old_a.get("title") or "").strip()
        if key and key not in seen:
            merged.append(old_a)
            seen.add(key)

    ai_cache[t_up] = {
        "updated_at": datetime.now().isoformat(),
        "articles": merged
    }
    save_ai_news_cache(ai_cache)


def get_pending_news(tickers: Optional[List[str]] = None, max_items: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    """
    Identifies news items that need AI translation and contextual analysis.
    Fetches raw news and filters out articles already analyzed by AI.
    """
    from src.news import fetch_stock_news_with_status

    if not tickers:
        from src.chart_data import load_candles_cache
        c = load_candles_cache()
        tickers = list(c.keys())

    pending: Dict[str, List[Dict[str, Any]]] = {}
    for t in tickers:
        t_up = t.upper().strip()
        articles, ok = fetch_stock_news_with_status(t_up, max_items=max_items)
        if not ok or not articles:
            continue
        t_pending = []
        for a in articles:
            existing = get_ai_analyzed_article(t_up, a.get("title", ""), a.get("link", ""))
            if not existing or not existing.get("ai_analyzed"):
                t_pending.append({
                    "ticker": t_up,
                    "title": a.get("title", ""),
                    "source": a.get("source", "News"),
                    "link": a.get("link", ""),
                    "published": a.get("published", ""),
                    "raw_date": a.get("raw_date", ""),
                    "current_sentiment": a.get("sentiment", "neutral")
                })
        if t_pending:
            pending[t_up] = t_pending
    return pending


def print_status() -> None:
    ai_cache = load_ai_news_cache()
    total_ai = sum(len(d.get("articles", [])) for d in ai_cache.values())
    print(f"📊 AI News Cache Status:")
    print(f"   Tickers analyzed: {len(ai_cache)}")
    print(f"   Total AI-analyzed articles: {total_ai}")
    for t, d in sorted(ai_cache.items()):
        arts = d.get("articles", [])
        print(f"   • {t:6}: {len(arts)} articles (updated: {d.get('updated_at', '-')[:19]})")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        print_status()
    elif len(sys.argv) > 1 and sys.argv[1] == "--pending":
        p = get_pending_news()
        print(json.dumps(p, ensure_ascii=False, indent=2))
    elif len(sys.argv) > 2 and sys.argv[1] == "--save":
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            data = json.load(f)
        for t, arts in data.items():
            merge_ai_articles(t, arts)
        print("Successfully merged AI news analysis!")
    else:
        print_status()
