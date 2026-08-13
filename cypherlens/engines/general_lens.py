"""
General Lens - Universal ad-free web scout and simplifier.
"""

import urllib.parse
from typing import List
from cypherlens.engines.base import SearchResultItem, LensResponse
from cypherlens.engines.search_client import execute_search


class GeneralLens:
    @staticmethod
    def search(query: str, max_results: int = 8) -> LensResponse:
        encoded_q = urllib.parse.quote(query)
        deep_links = [
            {"title": "🌐 Direct Web Search", "url": f"https://duckduckgo.com/?q={encoded_q}", "badge": "Ad-Free Search"},
        ]

        items: List[SearchResultItem] = []

        try:
            results = execute_search(query, max_results=max_results)
            seen_urls = set()

            for r in results:
                url = r.get("href") or ""
                title = r.get("title") or ""
                body = r.get("body") or ""

                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                domain = urllib.parse.urlparse(url).netloc.replace("www.", "")
                
                items.append(
                    SearchResultItem(
                        title=title,
                        url=url,
                        source=domain or "Web",
                        category="general",
                        badge="Intelligence",
                        snippet=body
                    )
                )
        except Exception:
            pass

        return LensResponse(
            query=query,
            detected_category="general",
            summary=f"Scouted {len(items)} web intelligence nodes for '{query}'.",
            items=items[:max_results],
            deep_links=deep_links
        )
