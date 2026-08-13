"""
Query Intent Classifier and Entity Extractor for CypherLens.
Detects whether a prompt is for flights, Amazon products, tech/gadgets, or general search.
"""

import re
from typing import Dict, Any, Optional


class QueryParser:
    FLIGHT_KEYWORDS = [
        "flight", "flights", "fly", "flying", "plane", "ticket", "airline",
        "from", "to", "trip", "roundtrip", "one way", "layover", "airport"
    ]
    
    AMAZON_KEYWORDS = [
        "amazon", "prime", "buy on amazon", "amazon.in", "amazon.com"
    ]
    
    TECH_KEYWORDS = [
        "laptop", "laptops", "gpu", "rtx", "gtx", "cpu", "processor", "ram",
        "pc", "monitor", "keyboard", "mouse", "headphone", "headphones",
        "earbuds", "phone", "smartphone", "iphone", "samsung", "pixel",
        "macbook", "oled", "4k", "tablet", "ipad", "console", "ps5", "xbox"
    ]

    @classmethod
    def classify_intent(cls, query: str) -> str:
        q_lower = query.lower()

        # Check explicit Amazon mention
        if any(w in q_lower for w in cls.AMAZON_KEYWORDS):
            return "amazon"

        # Check Flight patterns
        if any(w in q_lower for w in ["flight", "flights", "fly to", "plane to"]) or (
            "from " in q_lower and " to " in q_lower
        ):
            return "flight"

        # Check Tech patterns
        if any(w in q_lower for w in cls.TECH_KEYWORDS) or re.search(r"\b(rtx|gtx|intel|amd|ryzen|snapdragon)\b", q_lower):
            return "tech"

        # Check shopping/product intent
        if any(w in q_lower for w in ["buy", "price", "deals", "under $", "under ₹", "best price", "cheap", "cost of"]):
            return "amazon"

        return "general"

    @classmethod
    def parse_flight_entities(cls, query: str) -> Dict[str, Any]:
        """
        Extracts origin, destination, approximate dates from a flight query.
        e.g. 'flights from NYC to London in November' -> origin: NYC, destination: London, date: November
        """
        entities = {
            "origin": "",
            "destination": "",
            "date": "",
            "trip_type": "roundtrip"
        }
        q = query

        # Pattern: from <X> to <Y> [in/on/next <Z>]
        match = re.search(r"from\s+([A-Za-z\s]+?)\s+to\s+([A-Za-z\s]+?)(?:\s+(?:in|on|for|during|next)\s+(.+))?$", q, re.IGNORECASE)
        if match:
            entities["origin"] = match.group(1).strip()
            entities["destination"] = match.group(2).strip()
            if match.group(3):
                entities["date"] = match.group(3).strip()
        else:
            # Pattern: <X> to <Y>
            match2 = re.search(r"([A-Za-z\s]+?)\s+to\s+([A-Za-z\s]+?)(?:\s+(?:in|on|for|during|next)\s+(.+))?$", q, re.IGNORECASE)
            if match2:
                origin_candidate = match2.group(1).replace("flights", "").replace("flight", "").strip()
                entities["origin"] = origin_candidate
                entities["destination"] = match2.group(2).strip()
                if match2.group(3):
                    entities["date"] = match2.group(3).strip()

        if "one way" in q.lower() or "oneway" in q.lower():
            entities["trip_type"] = "oneway"

        return entities

    @classmethod
    def parse_budget_and_specs(cls, query: str) -> Dict[str, Any]:
        """
        Extracts price limits and tech specs from query.
        """
        info = {
            "budget": None,
            "currency": None,
            "specs": []
        }
        
        # Match "under 1000", "below $1200", "under ₹50000", "< 500"
        budget_match = re.search(r"(?:under|below|less than|<|budget of)\s*([$₹€£]?)\s*([\d,]+(?:\.\d+)?)\s*(k|kilo|usd|inr|eur|gbp)?", query, re.IGNORECASE)
        if budget_match:
            curr_symbol = budget_match.group(1) or ""
            amount_str = budget_match.group(2).replace(",", "")
            multiplier = budget_match.group(3) or ""
            
            try:
                amount = float(amount_str)
                if multiplier.lower() in ["k", "kilo"]:
                    amount *= 1000
                info["budget"] = amount
                info["currency"] = curr_symbol or ("USD" if not curr_symbol else curr_symbol)
            except ValueError:
                pass

        # Spec detection
        q_lower = query.lower()
        if "16gb" in q_lower or "32gb" in q_lower or "64gb" in q_lower or "8gb" in q_lower:
            spec = re.search(r"\b(\d+gb)\b", q_lower)
            if spec:
                info["specs"].append(f"RAM: {spec.group(1).upper()}")
        
        gpu_match = re.search(r"\b(rtx\s*\d{4}[a-z]?|gtx\s*\d{4}|rx\s*\d{4})\b", q_lower)
        if gpu_match:
            info["specs"].append(f"GPU: {gpu_match.group(1).upper()}")
            
        return info
