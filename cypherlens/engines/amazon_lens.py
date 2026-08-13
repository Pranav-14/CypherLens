"""
Amazon & E-Commerce Lens - Region-Aware Shopping Scout for European, Indian, and Global Retailers.
"""

import re
import urllib.parse
from typing import List, Optional
from cypherlens.engines.base import SearchResultItem, LensResponse
from cypherlens.engines.geo_resolver import GeoResolver
from cypherlens.engines.search_client import execute_search


class AmazonLens:
    @staticmethod
    def _extract_price(text: str, default_symbol: str = "€") -> str:
        # Match EUR, INR, USD, GBP with symbol or text
        match = re.search(r"([$₹€£]\s*[\d,]+(?:\.\d{2})?)", text)
        if match:
            return match.group(1).replace(" ", "")
        
        match2 = re.search(r"(?:EUR|USD|INR|GBP|Rs\.?|€|\$|₹|£)\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if match2:
            return f"{match2.group(0)}"
            
        # Match standalone German/European format "1.299 €" or "1299 €"
        match3 = re.search(r"([\d\.,]+)\s*(?:€|EUR|Euros?)", text, re.IGNORECASE)
        if match3:
            return f"{match3.group(1)} €"
            
        return ""

    @staticmethod
    def _extract_rating(text: str) -> str:
        match = re.search(r"(\d(?:\.\d)?)\s*(?:out of 5|\/5|\s*stars|\s*★|\s*von 5)", text, re.IGNORECASE)
        if match:
            return f"⭐ {match.group(1)}/5"
        return ""

    @staticmethod
    def _clean_product_url(url: str) -> str:
        """Strips tracking/affiliate clutter from URLs."""
        if "amazon." in url:
            dp_match = re.search(r"(https://www\.amazon\.[a-z\.]+/dp/[A-Z0-9]+)", url)
            if dp_match:
                return dp_match.group(1)
        return url

    @staticmethod
    def search(query: str, region: Optional[str] = None, max_results: int = 8) -> LensResponse:
        profile = GeoResolver.get_profile(region)
        clean_q = query.replace("amazon", "").replace("buy", "").strip() or query
        encoded_q = urllib.parse.quote(clean_q)

        # Build Regional Deep Hubs
        deep_links = []
        for hub in profile.get("hubs", []):
            url = hub["url_template"].format(query=encoded_q)
            deep_links.append({"title": hub["title"], "url": url, "badge": hub["badge"]})

        items: List[SearchResultItem] = []

        try:
            # Build targeted regional search
            search_domains = profile.get("search_sites", ["amazon.de", "idealo.de"])
            domain_filter = " OR ".join([f"site:{d}" for d in search_domains[:3]])
            search_query = f"{domain_filter} {clean_q}"
            
            results = execute_search(search_query, max_results=max_results)
            
            if len(results) < 3:
                fallback_query = f"{clean_q} price buy {profile['currency']} {profile['domain_amazon']}"
                results.extend(execute_search(fallback_query, max_results=max_results))

            seen_urls = set()
            for r in results:
                raw_url = r.get("href") or ""
                url = AmazonLens._clean_product_url(raw_url)
                title = r.get("title") or ""
                body = r.get("body") or ""

                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                combined_text = f"{title} {body}"
                price = AmazonLens._extract_price(combined_text, default_symbol=profile["currency_symbol"])
                rating = AmazonLens._extract_rating(combined_text)
                
                # Determine regional source badge
                source = profile["name"]
                if "amazon.de" in url:
                    source = "Amazon DE"
                elif "amazon.in" in url:
                    source = "Amazon IN"
                elif "amazon.com" in url:
                    source = "Amazon US"
                elif "idealo.de" in url:
                    source = "Idealo DE"
                elif "geizhals.de" in url:
                    source = "Geizhals DE"
                elif "mediamarkt" in url:
                    source = "MediaMarkt"
                elif "flipkart" in url:
                    source = "Flipkart"
                elif "bestbuy" in url:
                    source = "Best Buy"

                badge = f"{profile['flag']} {profile['currency']}"

                items.append(
                    SearchResultItem(
                        title=title,
                        url=url,
                        source=source,
                        category="amazon",
                        price=price if price else None,
                        rating=rating if rating else None,
                        badge=badge,
                        snippet=body
                    )
                )
        except Exception:
            pass

        return LensResponse(
            query=query,
            detected_category="amazon",
            summary=f"Scouted {len(items)} verified shopping deals in {profile['name']} ({profile['currency']}).",
            items=items[:max_results],
            deep_links=deep_links
        )
