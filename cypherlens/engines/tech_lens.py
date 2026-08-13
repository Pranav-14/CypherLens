"""
Tech Lens - Specialized hardware, laptop, and gadget radar.
Extracts specifications, performance tiers, price tags, and multi-retailer links.
"""

import re
import urllib.parse
from typing import List
from cypherlens.engines.base import SearchResultItem, LensResponse
from cypherlens.engines.search_client import execute_search


class TechLens:
    @staticmethod
    def _extract_specs(text: str) -> List[str]:
        specs = []
        # GPU detection
        gpu = re.search(r"\b(RTX\s*\d{4}(?:\s*Ti|\s*Super)?|GTX\s*\d{4}|Radeon\s*RX\s*\d{4}|Apple\s*M\d(?:\s*Pro|\s*Max)?)\b", text, re.IGNORECASE)
        if gpu:
            specs.append(f"GPU: {gpu.group(0).upper()}")
            
        # RAM detection
        ram = re.search(r"\b(\d{1,2}\s*GB(?:\s*DDR\d)?)\s*(?:RAM|Memory)?\b", text, re.IGNORECASE)
        if ram:
            specs.append(f"RAM: {ram.group(1).upper()}")

        # Storage detection
        storage = re.search(r"\b(\d{1,2}\s*TB|\d{3,4}\s*GB)\s*(?:SSD|NVMe|Storage)?\b", text, re.IGNORECASE)
        if storage:
            specs.append(f"Storage: {storage.group(1).upper()}")

        # Screen refresh / resolution
        display = re.search(r"\b(\d{2,3}Hz|OLED|4K|QHD|FHD|\d{2}(?:\.\d)?[\"']|\d{2}(?:\.\d)?\s*inch)\b", text, re.IGNORECASE)
        if display:
            specs.append(f"Display: {display.group(0)}")

        return specs

    @staticmethod
    def _extract_price(text: str) -> str:
        match = re.search(r"([$₹€£]\s*[\d,]+(?:\.\d{2})?)", text)
        if match:
            return match.group(1).replace(" ", "")
        match2 = re.search(r"(?:USD|INR|Rs\.?|EUR|GBP)\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if match2:
            return f"{match2.group(0)}"
        return ""

    @staticmethod
    def search(query: str, max_results: int = 8) -> LensResponse:
        encoded_q = urllib.parse.quote(query)
        
        deep_links = [
            {"title": "💻 Best Buy Hardware Hub", "url": f"https://www.bestbuy.com/site/searchpage.jsp?st={encoded_q}", "badge": "Best Buy"},
            {"title": "⚡ Newegg Tech Radar", "url": f"https://www.newegg.com/p/pl?d={encoded_q}", "badge": "Newegg"},
            {"title": "📦 Amazon Tech Deals", "url": f"https://www.amazon.com/s?k={encoded_q}", "badge": "Amazon"},
            {"title": "🔬 B&H Photo Video", "url": f"https://www.bhphotovideo.com/c/search?Ntt={encoded_q}", "badge": "B&H"},
        ]

        items: List[SearchResultItem] = []

        try:
            search_query = f"{query} price specs review buy deals"
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
                price = TechLens._extract_price(combined_text)
                specs = TechLens._extract_specs(combined_text)

                source = "Tech Retailer"
                if "amazon" in url:
                    source = "Amazon"
                elif "bestbuy" in url:
                    source = "Best Buy"
                elif "newegg" in url:
                    source = "Newegg"
                elif "tomshardware" in url:
                    source = "Tom's Hardware"
                elif "theverge" in url:
                    source = "The Verge"
                elif "gsmarena" in url:
                    source = "GSMArena"
                elif "notebookcheck" in url:
                    source = "NotebookCheck"
                elif "flipkart" in url:
                    source = "Flipkart"

                items.append(
                    SearchResultItem(
                        title=title,
                        url=url,
                        source=source,
                        category="tech",
                        price=price if price else None,
                        badge="Spec Matched" if specs else "Tech Scout",
                        specs=specs,
                        snippet=body
                    )
                )
        except Exception:
            pass

        return LensResponse(
            query=query,
            detected_category="tech",
            summary=f"Scouted {len(items)} tech hardware matches for '{query}'.",
            items=items[:max_results],
            deep_links=deep_links
        )
