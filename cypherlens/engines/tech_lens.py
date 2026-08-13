"""
Tech Lens - Region-Aware Hardware, Laptop, and Gadget Scout.
Extracts specifications, performance tiers, localized price tags, and multi-retailer links.
"""

import re
import urllib.parse
from typing import List, Optional
from cypherlens.engines.base import SearchResultItem, LensResponse
from cypherlens.engines.geo_resolver import GeoResolver
from cypherlens.engines.search_client import execute_search


class TechLens:
    @staticmethod
    def _extract_specs(text: str) -> List[str]:
        specs = []
        gpu = re.search(r"\b(RTX\s*\d{4}(?:\s*Ti|\s*Super)?|GTX\s*\d{4}|Radeon\s*RX\s*\d{4}|Apple\s*M\d(?:\s*Pro|\s*Max)?)\b", text, re.IGNORECASE)
        if gpu:
            specs.append(f"GPU: {gpu.group(0).upper()}")
            
        ram = re.search(r"\b(\d{1,2}\s*GB(?:\s*DDR\d)?)\s*(?:RAM|Memory)?\b", text, re.IGNORECASE)
        if ram:
            specs.append(f"RAM: {ram.group(1).upper()}")

        storage = re.search(r"\b(\d{1,2}\s*TB|\d{3,4}\s*GB)\s*(?:SSD|NVMe|Storage)?\b", text, re.IGNORECASE)
        if storage:
            specs.append(f"Storage: {storage.group(1).upper()}")

        display = re.search(r"\b(\d{2,3}Hz|OLED|4K|QHD|FHD|\d{2}(?:\.\d)?[\"']|\d{2}(?:\.\d)?\s*inch)\b", text, re.IGNORECASE)
        if display:
            specs.append(f"Display: {display.group(0)}")

        return specs

    @staticmethod
    def _extract_price(text: str, default_symbol: str = "€") -> str:
        match = re.search(r"([$₹€£]\s*[\d,]+(?:\.\d{2})?)", text)
        if match:
            return match.group(1).replace(" ", "")
        
        match2 = re.search(r"(?:EUR|USD|INR|GBP|Rs\.?|€|\$|₹|£)\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if match2:
            return f"{match2.group(0)}"

        match3 = re.search(r"([\d\.,]+)\s*(?:€|EUR|Euros?)", text, re.IGNORECASE)
        if match3:
            return f"{match3.group(1)} €"

        return ""

    @staticmethod
    def search(query: str, region: Optional[str] = None, max_results: int = 8) -> LensResponse:
        profile = GeoResolver.get_profile(region)
        encoded_q = urllib.parse.quote(query)

        # Build Regional Deep Hubs
        deep_links = []
        for hub in profile.get("hubs", []):
            url = hub["url_template"].format(query=encoded_q)
            deep_links.append({"title": hub["title"], "url": url, "badge": hub["badge"]})

        items: List[SearchResultItem] = []

        try:
            search_query = f"{query} price specs review buy {profile['currency']} {profile['domain_amazon']}"
            results = execute_search(search_query, max_results=max_results)

            seen_urls = set()
            for r in results:
                url = r.get("href") or ""
                title = r.get("title") or ""
                body = r.get("body") or ""

                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                combined_text = f"{title} {body}"
                price = TechLens._extract_price(combined_text, default_symbol=profile["currency_symbol"])
                specs = TechLens._extract_specs(combined_text)

                source = profile["name"]
                if "amazon.de" in url:
                    source = "Amazon DE"
                elif "idealo.de" in url:
                    source = "Idealo DE"
                elif "geizhals.de" in url:
                    source = "Geizhals DE"
                elif "mediamarkt" in url:
                    source = "MediaMarkt"
                elif "amazon.in" in url:
                    source = "Amazon IN"
                elif "flipkart" in url:
                    source = "Flipkart"
                elif "amazon.com" in url:
                    source = "Amazon US"
                elif "bestbuy" in url:
                    source = "Best Buy"
                elif "newegg" in url:
                    source = "Newegg"
                elif "tomshardware" in url:
                    source = "Tom's Hardware"
                elif "notebookcheck" in url:
                    source = "NotebookCheck"

                items.append(
                    SearchResultItem(
                        title=title,
                        url=url,
                        source=source,
                        category="tech",
                        price=price if price else None,
                        badge=f"{profile['flag']} Spec Matched" if specs else f"{profile['flag']} Tech Scout",
                        specs=specs,
                        snippet=body
                    )
                )
        except Exception:
            pass

        return LensResponse(
            query=query,
            detected_category="tech",
            summary=f"Scouted {len(items)} tech hardware deals in {profile['name']} ({profile['currency']}).",
            items=items[:max_results],
            deep_links=deep_links
        )
