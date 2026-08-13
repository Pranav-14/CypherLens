"""
Unified resilient search client for CypherLens.
Handles fallback between ddgs and duckduckgo_search with custom headers.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger("cypherlens")


def execute_search(query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """
    Executes a web search without requiring any API keys.
    Returns a list of dicts with keys: title, href, body.
    """
    results = []
    
    # 1. Try modern `ddgs`
    try:
        from ddgs import DDGS
        with DDGS() as ddgs_client:
            raw = list(ddgs_client.text(query, max_results=max_results))
            for item in raw:
                results.append({
                    "title": item.get("title") or "",
                    "href": item.get("href") or item.get("link") or "",
                    "body": item.get("body") or item.get("snippet") or ""
                })
        if results:
            return results
    except Exception as e:
        logger.debug(f"DDGS attempt failed: {e}")

    # 2. Try legacy `duckduckgo_search`
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs_client:
            raw = list(ddgs_client.text(query, max_results=max_results))
            for item in raw:
                results.append({
                    "title": item.get("title") or "",
                    "href": item.get("href") or item.get("link") or "",
                    "body": item.get("body") or item.get("snippet") or ""
                })
        if results:
            return results
    except Exception as e:
        logger.debug(f"duckduckgo_search attempt failed: {e}")

    return results
