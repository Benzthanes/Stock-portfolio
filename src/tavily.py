"""
Tavily Search API Client for Filter-Stock.
Provides programmatic web search for company fundamental updates, earnings dates,
and corporate event verification using standard library urllib only.
Zero external dependencies.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from src.http import DEFAULT_UA

TAVILY_API_URL = "https://api.tavily.com/search"
def get_tavily_api_key() -> str:
    """Returns the Tavily API key from TAVILY_API_KEY. The repo is public, so no key lives in code."""
    return os.getenv("TAVILY_API_KEY", "").strip()


def search_tavily(
    query: str,
    api_key: Optional[str] = None,
    max_results: int = 5,
    search_depth: str = "basic",
    include_answer: bool = False,
    include_raw_content: bool = False,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    timeout: float = 15.0,
) -> Dict[str, Any]:
    """
    Executes a web search query via Tavily Search API.
    Returns the parsed JSON response dict containing 'results', 'query', etc.
    """
    if api_key is not None:
        key = api_key.strip()
    else:
        key = get_tavily_api_key().strip()
    if not key:
        raise ValueError("Tavily API key is missing. Set TAVILY_API_KEY or provide api_key.")

    payload: Dict[str, Any] = {
        "api_key": key,
        "query": query,
        "max_results": max(1, min(max_results, 20)),
        "search_depth": search_depth if search_depth in ("basic", "advanced") else "basic",
        "include_answer": include_answer,
        "include_raw_content": include_raw_content,
    }
    if include_domains:
        payload["include_domains"] = include_domains
    if exclude_domains:
        payload["exclude_domains"] = exclude_domains

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        TAVILY_API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": DEFAULT_UA,
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        res_data = resp.read().decode("utf-8")
        return json.loads(res_data)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m src.tavily <query>", file=sys.stderr)
        sys.exit(1)
    query = " ".join(sys.argv[1:])
    try:
        res = search_tavily(query, max_results=3)
        results = res.get("results", [])
        print(f"Query: {query}")
        print(f"Results ({len(results)}):")
        for i, r in enumerate(results, 1):
            print(f"\n[{i}] {r.get('title')}")
            print(f"    URL: {r.get('url')}")
            content = r.get("content", "").replace("\n", " ").strip()
            if len(content) > 160:
                content = content[:157] + "..."
            print(f"    Snippet: {content}")
    except Exception as e:
        print(f"Error querying Tavily: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
