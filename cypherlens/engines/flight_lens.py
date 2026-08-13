"""
Flight Lens - Real-time flight search, route intelligence, and 1-click deep radar links.
"""

import urllib.parse
from typing import List
from cypherlens.engines.base import SearchResultItem, LensResponse
from cypherlens.engines.query_parser import QueryParser
from cypherlens.engines.search_client import execute_search


class FlightLens:
    @staticmethod
    def search(query: str, max_results: int = 6) -> LensResponse:
        entities = QueryParser.parse_flight_entities(query)
        origin = entities.get("origin") or "Your Airport"
        destination = entities.get("destination") or "Destination"
        date_str = entities.get("date") or ""

        # Build deep radar booking links
        q_encoded = urllib.parse.quote(f"flights from {origin} to {destination} {date_str}".strip())
        google_flights_url = f"https://www.google.com/travel/flights?q={q_encoded}"
        kayak_url = f"https://www.kayak.com/flights?query={q_encoded}"
        skyscanner_url = f"https://www.skyscanner.com/transport/flights-from/{urllib.parse.quote(origin)}/to/{urllib.parse.quote(destination)}/"

        deep_links = [
            {"title": "✈️ Google Flights Live Radar", "url": google_flights_url, "badge": "Live Route Radar"},
            {"title": "🔍 Skyscanner Price Matrix", "url": skyscanner_url, "badge": "Price Matrix"},
            {"title": "🌐 Kayak Deal Compare", "url": kayak_url, "badge": "Aggregator"},
        ]

        items: List[SearchResultItem] = []
        
        # Primary Route Card
        primary_title = f"Flight Route: {origin.upper()} ➔ {destination.upper()}"
        if date_str:
            primary_title += f" ({date_str})"
            
        items.append(
            SearchResultItem(
                title=primary_title,
                url=google_flights_url,
                source="Google Flights",
                category="flight",
                badge="⚡ Live Route Radar",
                snippet=f"Direct route scan from {origin} to {destination}. Click to view cheapest dates, airlines, baggage rules, and non-stop flight schedules.",
                specs=[f"From: {origin}", f"To: {destination}", f"Date: {date_str or 'Flexible'}"]
            )
        )

        try:
            search_q = f"cheapest flights from {origin} to {destination} {date_str} airlines fares"
            results = execute_search(search_q, max_results=max_results)
            
            seen_urls = {google_flights_url}
            for r in results:
                url = r.get("href") or ""
                title = r.get("title") or ""
                body = r.get("body") or ""
                
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                source = "Airlines / Travel"
                if "google.com" in url:
                    source = "Google Flights"
                elif "skyscanner" in url:
                    source = "Skyscanner"
                elif "kayak" in url:
                    source = "Kayak"
                elif "makemytrip" in url:
                    source = "MakeMyTrip"
                elif "expedia" in url:
                    source = "Expedia"
                elif "tripadvisor" in url:
                    source = "TripAdvisor"

                items.append(
                    SearchResultItem(
                        title=title,
                        url=url,
                        source=source,
                        category="flight",
                        badge="Airline Deal",
                        snippet=body
                    )
                )
        except Exception:
            pass

        return LensResponse(
            query=query,
            detected_category="flight",
            summary=f"Scouted flight route intelligence for {origin} ➔ {destination}.",
            items=items,
            deep_links=deep_links
        )
