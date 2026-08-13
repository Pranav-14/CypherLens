"""
Geographic resolver & Regional Retailer Profiles for CypherLens.
Maps cities to IATA airport codes, defines regional e-commerce hubs, and handles auto-detection.
"""

import locale
import time
from typing import Dict, Any, Optional

# Comprehensive IATA airport code dictionary
AIRPORT_IATA_MAP: Dict[str, str] = {
    # Germany & DACH
    "frankfurt": "FRA",
    "frankfurt am main": "FRA",
    "munich": "MUC",
    "münchen": "MUC",
    "berlin": "BER",
    "hamburg": "HAM",
    "cologne": "CGN",
    "köln": "CGN",
    "dusseldorf": "DUS",
    "düsseldorf": "DUS",
    "stuttgart": "STR",
    "vienna": "VIE",
    "wien": "VIE",
    "zurich": "ZRH",
    "zürich": "ZRH",
    "geneva": "GVA",
    
    # Europe
    "london": "LON",
    "heathrow": "LHR",
    "gatwick": "LGW",
    "paris": "PAR",
    "charles de gaulle": "CDG",
    "orly": "ORY",
    "amsterdam": "AMS",
    "schiphol": "AMS",
    "brussels": "BRU",
    "madrid": "MAD",
    "barcelona": "BCN",
    "rome": "FCO",
    "milan": "MXP",
    "lisbon": "LIS",
    "dublin": "DUB",
    "copenhagen": "CPH",
    "stockholm": "ARN",
    "oslo": "OSL",
    "helsinki": "HEL",
    "athens": "ATH",
    "warsaw": "WAW",
    "prague": "PRG",
    "budapest": "BUD",
    "istanbul": "IST",
    
    # India
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "hyderabad": "HYD",
    "chennai": "MAA",
    "madras": "MAA",
    "kolkata": "CCU",
    "calcutta": "CCU",
    "kochi": "COK",
    "cochin": "COK",
    "ahmedabad": "AMD",
    "pune": "PNQ",
    "goa": "GOI",
    "jaipur": "JAI",
    "lucknow": "LKO",
    "trivandrum": "TRV",
    "thiruvananthapuram": "TRV",
    "chandigarh": "IXC",
    "amritsar": "ATQ",
    "guwahati": "GAU",
    
    # United States & Canada
    "new york": "NYC",
    "nyc": "NYC",
    "jfk": "JFK",
    "newark": "EWR",
    "laguardia": "LGA",
    "san francisco": "SFO",
    "sfo": "SFO",
    "los angeles": "LAX",
    "lax": "LAX",
    "chicago": "ORD",
    "seattle": "SEA",
    "boston": "BOS",
    "miami": "MIA",
    "dallas": "DFW",
    "austin": "AUS",
    "houston": "IAH",
    "atlanta": "ATL",
    "las vegas": "LAS",
    "washington": "WAS",
    "denver": "DEN",
    "toronto": "YYZ",
    "vancouver": "YVR",
    "montreal": "YUL",
    
    # Asia & Middle East
    "tokyo": "TYO",
    "narita": "NRT",
    "haneda": "HND",
    "singapore": "SIN",
    "dubai": "DXB",
    "abu dhabi": "AUH",
    "doha": "DOH",
    "bangkok": "BKK",
    "kuala lumpur": "KUL",
    "hong kong": "HKG",
    "seoul": "ICN",
    "taipei": "TPE",
    "bali": "DPS",
    "denpasar": "DPS",
    "sydney": "SYD",
    "melbourne": "MEL",
    "auckland": "AKL"
}

# Regional Profiles
REGIONAL_PROFILES: Dict[str, Dict[str, Any]] = {
    "de": {
        "name": "Germany & EU",
        "flag": "🇩🇪",
        "currency": "EUR",
        "currency_symbol": "€",
        "domain_amazon": "amazon.de",
        "search_sites": ["amazon.de", "idealo.de", "geizhals.de", "mediamarkt.de", "otto.de"],
        "hubs": [
            {"title": "📦 Amazon.de Direct Hub", "url_template": "https://www.amazon.de/s?k={query}", "badge": "Amazon.de"},
            {"title": "🏷️ Idealo.de Price Compare", "url_template": "https://www.idealo.de/preisvergleich/MainSearchProductCategory.html?q={query}", "badge": "Idealo.de"},
            {"title": "⚡ Geizhals Hardware Radar", "url_template": "https://geizhals.de/?fs={query}", "badge": "Geizhals.de"},
            {"title": "🛒 MediaMarkt Deals", "url_template": "https://www.mediamarkt.de/de/search.html?query={query}", "badge": "MediaMarkt"},
        ]
    },
    "in": {
        "name": "India",
        "flag": "🇮🇳",
        "currency": "INR",
        "currency_symbol": "₹",
        "domain_amazon": "amazon.in",
        "search_sites": ["amazon.in", "flipkart.com", "croma.com", "reliancedigital.in"],
        "hubs": [
            {"title": "📦 Amazon India Hub", "url_template": "https://www.amazon.in/s?k={query}", "badge": "Amazon.in"},
            {"title": "🛍️ Flipkart Deal Matrix", "url_template": "https://www.flipkart.com/search?q={query}", "badge": "Flipkart"},
            {"title": "⚡ Croma Electronics", "url_template": "https://www.croma.com/searchB?q={query}", "badge": "Croma"},
            {"title": "🛒 Reliance Digital", "url_template": "https://www.reliancedigital.in/search?q={query}", "badge": "Reliance Digital"},
        ]
    },
    "us": {
        "name": "United States",
        "flag": "🇺🇸",
        "currency": "USD",
        "currency_symbol": "$",
        "domain_amazon": "amazon.com",
        "search_sites": ["amazon.com", "bestbuy.com", "newegg.com", "bhphotovideo.com"],
        "hubs": [
            {"title": "📦 Amazon US Direct Hub", "url_template": "https://www.amazon.com/s?k={query}", "badge": "Amazon.com"},
            {"title": "💻 Best Buy Hardware Hub", "url_template": "https://www.bestbuy.com/site/searchpage.jsp?st={query}", "badge": "Best Buy"},
            {"title": "⚡ Newegg Tech Radar", "url_template": "https://www.newegg.com/p/pl?d={query}", "badge": "Newegg"},
            {"title": "🔬 B&H Photo Video", "url_template": "https://www.bhphotovideo.com/c/search?Ntt={query}", "badge": "B&H"},
        ]
    },
    "uk": {
        "name": "United Kingdom",
        "flag": "🇬🇧",
        "currency": "GBP",
        "currency_symbol": "£",
        "domain_amazon": "amazon.co.uk",
        "search_sites": ["amazon.co.uk", "currys.co.uk", "argos.co.uk", "ebuyer.com"],
        "hubs": [
            {"title": "📦 Amazon UK Hub", "url_template": "https://www.amazon.co.uk/s?k={query}", "badge": "Amazon.co.uk"},
            {"title": "💻 Currys PC World", "url_template": "https://www.currys.co.uk/search?q={query}", "badge": "Currys"},
            {"title": "🛍️ Argos Deals", "url_template": "https://www.argos.co.uk/search/{query}", "badge": "Argos"},
        ]
    }
}


class GeoResolver:
    @staticmethod
    def resolve_iata(city_or_airport: str) -> Optional[str]:
        """Resolves city name or airport to a 3-letter IATA code."""
        if not city_or_airport:
            return None
            
        clean = city_or_airport.lower().strip()
        # Direct lookup
        if clean in AIRPORT_IATA_MAP:
            return AIRPORT_IATA_MAP[clean]
            
        # If already a 3-letter uppercase code
        if len(clean) == 3 and clean.isalpha():
            return clean.upper()

        # Partial matching
        for name, code in AIRPORT_IATA_MAP.items():
            if name in clean or clean in name:
                return code
                
        return None

    @staticmethod
    def detect_region() -> str:
        """Auto-detects region from system locale / timezone."""
        try:
            loc = locale.getdefaultlocale()[0] or ""
            loc_lower = loc.lower()
            if "de" in loc_lower or "at" in loc_lower or "ch" in loc_lower or "fr" in loc_lower or "it" in loc_lower or "es" in loc_lower or "nl" in loc_lower:
                return "de"
            elif "in" in loc_lower:
                return "in"
            elif "gb" in loc_lower or "uk" in loc_lower:
                return "uk"
        except Exception:
            pass

        # Check timezone string
        tz_name = time.tzname[0].lower() if time.tzname else ""
        if "cest" in tz_name or "cet" in tz_name or "eet" in tz_name or "wet" in tz_name:
            return "de"
        elif "ist" in tz_name:
            return "in"
        elif "gmt" in tz_name or "bst" in tz_name:
            return "uk"

        return "de"  # Default to Germany/EU

    @staticmethod
    def get_profile(region_code: Optional[str] = None) -> Dict[str, Any]:
        """Gets the regional configuration profile."""
        code = (region_code or "").lower()
        if code not in REGIONAL_PROFILES or code == "auto":
            code = GeoResolver.detect_region()
            
        profile = REGIONAL_PROFILES.get(code, REGIONAL_PROFILES["de"]).copy()
        profile["code"] = code
        return profile
