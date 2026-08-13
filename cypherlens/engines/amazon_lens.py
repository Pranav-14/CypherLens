"""
Amazon Lens - Scouts Amazon and top eCommerce platforms for real-time product prices, ratings, and clean buy links.
"""

import re
import urllib.parse
from typing import List
from cypherlens.engines.base import SearchResultItem, LensResponse
from cypherlens.engines.search_client import execute_search


class AmazonLens:
    @staticmethod
    def _extract_price(text: str) -> str:
        # Match currency symbols followed by numbers: $499, ₹49,990, €399, £250
        match = re.search(r"([$₹€£]\s*[\d,]+(?:\.\d{2})?)", text)
        if match:
            return match.group(1).replace(" ", "")
        
        # Match "USD 499", "Rs. 49,990", "INR 15,000"
        match2 = re.search(r"(?:USD|INR|Rs\.?|EUR|GBP)\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if match2:
            return f"{match2.group(0)}"
            
        return ""

    @staticmethod
    def _extract_rating(text: str) -> str:
        # Match "4.5 out of 5 stars", "4.6/5", "★ 4.4"
        match = re.search(r"(\d(?:\.\d)?)\s*(?:out of 5|\/5|\s*stars|\s*★)", text, re.IGNORECASE)
        if match:
            return f"⭐ {match.group(1)}/5"
        return ""

    @staticmethod
    def _clean_amazon_url(url: str) -> str:
        """Strips noisy referral/tracking parameters from product URLs."""
        if "amazon." in url:
            # Extract dp/ASIN if present
            dp_match = re.search(r"(https://www\.amazon\.[a-z\.]+/dp/[A-Z0-9]+)", url)
            if dp_match:
                return dp_match.group(1)
        return url

    @staticmethod
    def search(query: str, max_results: int = 8) -> LensResponse:
        clean_q = query.replace("amazon", "").replace("buy", "").strip() or query
        encoded_q = urllib.parse.quote(clean_q)
        
        amazon_us_url = f"https://www.amazon.com/s?k={encoded_q}"
        amazon_in_url = f"https://www.amazon.in/s?k={encoded_q}"

        deep_links = [
            {"title": "📦 Amazon US Direct Hub", "url": amazon_us_url, "badge": "Amazon.com"},
            {"title": "🇮🇳 Amazon India Direct Hub", "url": amazon_in_url, "badge": "Amazon.in"},
        ]

        items: List[SearchResultItem] = []

        try:
            # Query targeting Amazon and trusted retailers
            search_query = f"site:amazon.com OR site:amazon.in {clean_q}"
            results = execute_search(search_query, max_results=max_results)
            
            # If specific site search yielded few results, fallback to general product search
            if len(results) < 3:
                fallback_results = execute_search(f"{clean_q} price amazon buy deals", max_results=max_results)
                results.extend(fallback_results)

            seen_urls = set()
            for r in results:
                raw_url = r.get("href") or ""
                url = AmazonLens._clean_amazon_url(raw_url)
                title = r.get("title") or ""
                body = r.get("body") or ""

                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                combined_text = f"{title} {body}"
                price = AmazonLens._extract_price(combined_text)
                rating = AmazonLens._extract_rating(combined_text)
                
                source = "Amazon"
                if "amazon.in" in url:
                    source = "Amazon IN"
                elif "amazon.com" in url:
                    source = "Amazon US"
                elif "walmart" in url:
                    source = "Walmart"
                elif "bestbuy" in url:
                    source = "Best Buy"
                elif "target.com" in url:
                    source = "Target"

                badge = "Prime Deal" if "prime" in combined_text.lower() else "Verified Store"

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
            summary=f"Scouted {len(items)} product intelligence records for '{clean_q}'.",
            items=items[:max_results],
            deep_links=deep_links
        )
