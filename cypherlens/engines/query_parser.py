"""
Query Intent Classifier and Entity Extractor for CypherLens.
Detects whether a prompt is for flights, Amazon/shopping products, tech/gadgets, or general search.
"""

import re
from typing import Dict, Any, Optional
from cypherlens.engines.geo_resolver import AIRPORT_IATA_MAP, GeoResolver


class QueryParser:
    FLIGHT_KEYWORDS = [
        "flight", "flights", "fly", "flying", "plane", "ticket", "tickets", "airline", "airlines",
        "trip", "roundtrip", "one way", "oneway", "layover", "airport", "nonstop", "non-stop"
    ]
    
    AMAZON_KEYWORDS = [
        "amazon", "prime", "buy on amazon", "amazon.de", "amazon.in", "amazon.com", "idealo", "flipkart"
    ]
    
    TECH_KEYWORDS = [
        "laptop", "laptops", "gpu", "rtx", "gtx", "cpu", "processor", "ram",
        "pc", "monitor", "monitors", "keyboard", "keyboards", "mouse", "headphone", "headphones",
        "earbuds", "phone", "phones", "smartphone", "smartphones", "iphone", "samsung", "pixel",
        "macbook", "oled", "4k", "tablet", "ipad", "console", "ps5", "xbox", "geforce", "radeon"
    ]

    @classmethod
    def classify_intent(cls, query: str) -> str:
        q_lower = query.lower()

        # 1. Explicit keyword check for flights
        if any(w in q_lower for w in cls.FLIGHT_KEYWORDS):
            return "flight"

        # 2. Check "<City1> to <City2>" flight pattern (e.g. "frankfurt to bangalore")
        to_match = re.search(r"([a-z\s]+?)\s+to\s+([a-z\s]+)", q_lower)
        if to_match:
            c1 = to_match.group(1).replace("flights", "").replace("flight", "").strip().split(" ")[-1]
            c2 = to_match.group(2).strip().split(" ")[0]
            if GeoResolver.resolve_iata(c1) or GeoResolver.resolve_iata(c2):
                return "flight"

        # 3. Explicit Shopping / Amazon check
        if any(w in q_lower for w in cls.AMAZON_KEYWORDS):
            return "amazon"

        # 4. Tech check
        if any(w in q_lower for w in cls.TECH_KEYWORDS) or re.search(r"\b(rtx\s*\d{4}|gtx\s*\d{4}|intel|amd|ryzen|snapdragon|m\d\s*chip)\b", q_lower):
            return "tech"

        # 5. Generic shopping intent
        if any(w in q_lower for w in ["buy", "price", "deals", "under €", "under $", "under ₹", "best price", "cheap", "cost of", "euros"]):
            return "amazon"

        return "general"

    @classmethod
    def parse_flight_entities(cls, query: str) -> Dict[str, Any]:
        """
        Extracts origin, destination, and dates from a flight query.
        """
        entities = {
            "origin": "",
            "destination": "",
            "date": "",
            "trip_type": "roundtrip"
        }
        q_clean = query

        # Pattern: from <X> to <Y>
        match_from_to = re.search(r"from\s+([A-Za-z\s]+?)\s+to\s+([A-Za-z\s]+?)(?:\s+(?:in|on|for|during|next|december|january|february|march|april|may|june|july|august|september|october|november|dec|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov)\b|\d{1,2}|$)", q_clean, re.IGNORECASE)
        if match_from_to:
            entities["origin"] = match_from_to.group(1).strip()
            entities["destination"] = match_from_to.group(2).strip()
        else:
            # Pattern: <X> to <Y> (e.g. frankfurt to bangalore)
            match_to = re.search(r"([A-Za-z\s]+?)\s+to\s+([A-Za-z\s]+?)(?:\s+(?:in|on|for|during|next|december|january|february|march|april|may|june|july|august|september|october|november|dec|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov)\b|\d{1,2}|$)", q_clean, re.IGNORECASE)
            if match_to:
                cand1 = match_to.group(1).replace("flights", "").replace("flight", "").strip()
                entities["origin"] = cand1
                entities["destination"] = match_to.group(2).strip()

        return entities

    @classmethod
    def parse_budget_and_specs(cls, query: str) -> Dict[str, Any]:
        info = {
            "budget": None,
            "currency": None,
            "specs": []
        }
        
        budget_match = re.search(r"(?:under|below|less than|<|budget of)\s*([$₹€£]?)\s*([\d,]+(?:\.\d+)?)\s*(k|kilo|usd|inr|eur|gbp|euros?|rupees?|dollars?)?", query, re.IGNORECASE)
        if budget_match:
            curr_symbol = budget_match.group(1) or ""
            amount_str = budget_match.group(2).replace(",", "")
            multiplier = budget_match.group(3) or ""
            
            try:
                amount = float(amount_str)
                if multiplier.lower() in ["k", "kilo"]:
                    amount *= 1000
                info["budget"] = amount
                info["currency"] = curr_symbol or "EUR"
            except ValueError:
                pass

        q_lower = query.lower()
        if "16gb" in q_lower or "32gb" in q_lower or "64gb" in q_lower or "8gb" in q_lower:
            spec = re.search(r"\b(\d+gb)\b", q_lower)
            if spec:
                info["specs"].append(f"RAM: {spec.group(1).upper()}")
        
        gpu_match = re.search(r"\b(rtx\s*\d{4}[a-z]?|gtx\s*\d{4}|rx\s*\d{4})\b", q_lower)
        if gpu_match:
            info["specs"].append(f"GPU: {gpu_match.group(1).upper()}")
            
        return info
