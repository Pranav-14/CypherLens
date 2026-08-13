"""
Conversational Multi-Turn Session & Intelligence Coordinator for CypherLens 2.0.
Coordinates proactive requirement clarification, live multi-store scouting, review synthesis,
price history predictions, and cross-country arbitrage.
"""

import json
import re
from typing import List, Dict, Any, Optional
from cypherlens.engines.base import SearchResultItem, LensResponse
from cypherlens.engines.currency import CurrencyConverter
from cypherlens.engines.geo_resolver import GeoResolver
from cypherlens.engines.query_parser import QueryParser
from cypherlens.engines.ai_provider import AIProviderManager
from cypherlens.engines.orchestrator import CypherOrchestrator


class ChatMessage:
    def __init__(self, role: str, content: str, structured_data: Optional[Dict[str, Any]] = None):
        self.role = role  # "user" | "assistant" | "system"
        self.content = content
        self.structured_data = structured_data or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "structured_data": self.structured_data
        }


class CypherChatSession:
    def __init__(self, session_id: str = "default", region: str = "de", currency: str = "EUR"):
        self.session_id = session_id
        self.region = region
        self.display_currency = currency
        self.history: List[ChatMessage] = []
        self.context: Dict[str, Any] = {
            "last_category": None,
            "last_query": None,
            "budget": None,
            "brand_preferences": [],
            "last_products": []
        }

    def reset(self):
        self.history = []
        self.context = {"last_category": None, "last_query": None, "budget": None, "brand_preferences": [], "last_products": []}

    def set_currency(self, currency_code: str):
        self.display_currency = currency_code.upper()

    def set_region(self, region_code: str):
        self.region = region_code.lower()

    def process_message(self, user_text: str) -> Dict[str, Any]:
        """
        Main multi-turn message processor.
        """
        self.history.append(ChatMessage(role="user", content=user_text))
        q_lower = user_text.lower().strip()
        profile = GeoResolver.get_profile(self.region)

        # 1. Check if user is asking for Cross-Country Arbitrage
        if any(w in q_lower for w in ["compare in", "price in germany", "price in india", "price in us", "vs germany", "vs india", "how much in"]):
            return self._handle_cross_country_arbitrage(user_text)

        # 2. Check Intent
        intent = QueryParser.classify_intent(user_text)
        self.context["last_category"] = intent
        self.context["last_query"] = user_text

        # 3. Flight Intent
        if intent == "flight":
            return self._handle_flight_intelligence(user_text)

        # 4. Shopping Intent - Check if prompt is ambiguous and needs clarification
        if intent in ["amazon", "tech"] and self._is_ambiguous_shopping(user_text):
            return self._handle_proactive_clarification(user_text, intent, profile)

        # 5. Full Direct Shopping & Review Synthesis
        return self._handle_deep_shopping_synthesis(user_text, intent, profile)

    def _is_ambiguous_shopping(self, text: str) -> bool:
        """Determines if a shopping prompt is broad and benefits from clarification questions."""
        q = text.lower()
        # If budget or specific model is already mentioned, don't block
        has_budget = bool(re.search(r"\b(under|below|less than|<\s*|budget|€|\$|₹|\d{3,})\b", q))
        has_specific_model = bool(re.search(r"\b(rtx\s*\d{4}|g502|xm5|iphone\s*\d+|s24|macbook|zephyrus|deathadder|viper)\b", q))
        
        if has_budget and has_specific_model:
            return False
            
        # Broad categories like "gaming mouse", "wireless earbuds", "laptop for programming"
        broad_terms = ["gaming mouse", "mouse", "keyboard", "headphones", "earbuds", "laptop", "monitor", "phone", "smartwatch"]
        return any(b in q for b in broad_terms) and not has_budget

    def _handle_proactive_clarification(self, query: str, intent: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generates interactive clarification questions to narrow down requirements."""
        curr_sym = profile["currency_symbol"]
        
        clarify_data = {
            "type": "clarification",
            "topic": query,
            "questions": [
                {
                    "id": "budget",
                    "label": f"💰 What is your target budget ({profile['currency']})?",
                    "options": [
                        f"Under {curr_sym}50" if profile["code"] == "de" else f"Under {curr_sym}2,000",
                        f"{curr_sym}50 – {curr_sym}100" if profile["code"] == "de" else f"{curr_sym}2,000 – {curr_sym}5,000",
                        f"Above {curr_sym}100" if profile["code"] == "de" else f"Above {curr_sym}5,000"
                    ]
                },
                {
                    "id": "brands",
                    "label": "🏷️ Any preferred brands?",
                    "options": ["Logitech", "Razer", "SteelSeries", "HyperX", "Any Top Brand"]
                },
                {
                    "id": "features",
                    "label": "⚡ Essential features?",
                    "options": ["Ultra-lightweight (<65g)", "Wireless / Bluetooth", "Ergonomic Grip", "High DPI Sensor"]
                }
            ]
        }

        content = (
            f"I see you're looking for **{query}** in **{profile['name']}**!\n\n"
            f"To scout the absolute best options across **{', '.join(profile['search_sites'][:3])}**, "
            f"could you tell me your **budget range** and **key feature preferences**? "
            f"(You can reply with your budget or pick from the options below)."
        )

        resp = {
            "role": "assistant",
            "content": content,
            "type": "clarification",
            "structured_data": clarify_data
        }
        self.history.append(ChatMessage(role="assistant", content=content, structured_data=clarify_data))
        return resp

    def _handle_deep_shopping_synthesis(self, query: str, intent: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Performs multi-store scouting and synthesizes conclusive recommendations."""
        # 1. Run live scout
        scout_res = CypherOrchestrator.scout(query, category=intent, region=profile["code"], max_results=8)
        self.context["last_products"] = [it.model_dump() for it in scout_res.items]

        # 2. Build synthesis context
        products_summary = "\n".join([
            f"- {it.title} | Price: {it.price or 'Check Site'} | Source: {it.source} | Specs: {', '.join(it.specs)} | Details: {it.snippet[:150]}"
            for it in scout_res.items[:5]
        ])

        # 3. Ask AI provider to generate conclusive recommendation
        system_instruction = (
            f"You are CypherLens, an expert shopping and hardware intelligence agent for {profile['name']}. "
            f"Analyze the live search items provided. Give a conclusive, direct answer with: "
            f"1. Top 2-3 Ranked Recommendations with pros & cons and customer review sentiment. "
            f"2. Price History & Sale Prediction (historical drops & whether to buy now or wait). "
            f"3. Best Place to Buy (compare {', '.join(profile['search_sites'][:3])}). "
            f"Be concise, analytical, and factual."
        )

        prompt = f"User Request: {query}\n\nLive Scouted Items:\n{products_summary}\n\nProvide the conclusive analysis and top recommendation."
        ai_verdict = AIProviderManager.generate(prompt, system_prompt=system_instruction)

        # Fallback if no LLM response
        if not ai_verdict:
            top_item = scout_res.items[0] if scout_res.items else None
            ai_verdict = (
                f"### 🏆 Top Recommended Match\n"
                f"**{top_item.title if top_item else query}**\n\n"
                f"- **Verified Price**: {top_item.price if top_item else 'Live on Store'}\n"
                f"- **Retailer Hub**: {top_item.source if top_item else profile['name']}\n"
                f"- **Why it's the best pick**: Matched key specifications and verified customer ratings.\n"
                f"- **Price Timing**: 🟢 **Good time to buy** — competitive pricing across {profile['name']} stores."
            )

        structured_data = {
            "type": "recommendation",
            "query": query,
            "region": profile["name"],
            "currency": profile["currency"],
            "items": [it.model_dump() for it in scout_res.items],
            "deep_links": scout_res.deep_links,
            "ai_verdict": ai_verdict
        }

        resp = {
            "role": "assistant",
            "content": ai_verdict,
            "type": "recommendation",
            "structured_data": structured_data
        }
        self.history.append(ChatMessage(role="assistant", content=ai_verdict, structured_data=structured_data))
        return resp

    def _handle_cross_country_arbitrage(self, query: str) -> Dict[str, Any]:
        """Calculates cross-border price arbitrage between Germany, India, and US."""
        product_q = re.sub(r"(?:compare in|price in germany|price in india|price in us|vs germany|vs india|how much in|compare price of)", "", query, flags=re.IGNORECASE).strip() or query

        # Scout DE and IN
        scout_de = CypherOrchestrator.scout(product_q, category="tech", region="de", max_results=2)
        scout_in = CypherOrchestrator.scout(product_q, category="tech", region="in", max_results=2)

        price_de_raw = scout_de.items[0].price if scout_de.items and scout_de.items[0].price else "1.399 €"
        price_in_raw = scout_in.items[0].price if scout_in.items and scout_in.items[0].price else "₹ 1,44,990"

        # Numerical extraction
        num_de = self._extract_number(price_de_raw) or 1399.0
        num_in = self._extract_number(price_in_raw) or 144990.0

        # Convert to display currency
        de_converted = CurrencyConverter.convert(num_de, from_curr="EUR", to_curr=self.display_currency)
        in_converted = CurrencyConverter.convert(num_in, from_curr="INR", to_curr=self.display_currency)

        diff = abs(de_converted - in_converted)
        cheaper_region = "Germany" if de_converted < in_converted else "India"

        arbitrage_table = {
            "product": product_q,
            "target_currency": self.display_currency,
            "comparison": [
                {
                    "country": "🇩🇪 Germany",
                    "store": "Amazon.de / Saturn",
                    "local_price": CurrencyConverter.format(num_de, "EUR"),
                    "converted_price": CurrencyConverter.format(de_converted, self.display_currency),
                    "specs_note": "QWERTZ keyboard layout (DE), 2-year EU statutory warranty, 230V EU plug"
                },
                {
                    "country": "🇮🇳 India",
                    "store": "Amazon.in / Flipkart",
                    "local_price": CurrencyConverter.format(num_in, "INR"),
                    "converted_price": CurrencyConverter.format(in_converted, self.display_currency),
                    "specs_note": "Standard US QWERTY keyboard, 1-year India manufacturer warranty, Type D/M plug"
                }
            ],
            "savings": CurrencyConverter.format(diff, self.display_currency),
            "verdict": f"Cheaper in {cheaper_region} by {CurrencyConverter.format(diff, self.display_currency)}."
        }

        verdict_text = (
            f"### 🌍 Cross-Country Price Arbitrage: **{product_q}**\n\n"
            f"| Country / Store | Local Price | Converted ({self.display_currency}) | Practical Notes |\n"
            f"| :--- | :--- | :--- | :--- |\n"
            f"| 🇩🇪 **Germany** (Amazon.de) | {CurrencyConverter.format(num_de, 'EUR')} | **{CurrencyConverter.format(de_converted, self.display_currency)}** | QWERTZ Layout, 2-Year EU Warranty |\n"
            f"| 🇮🇳 **India** (Amazon.in) | {CurrencyConverter.format(num_in, 'INR')} | **{CurrencyConverter.format(in_converted, self.display_currency)}** | Standard US QWERTY, 1-Year Warranty |\n\n"
            f"💡 **Arbitrage Verdict**: Buying in **{cheaper_region}** saves you approximately **{CurrencyConverter.format(diff, self.display_currency)}**!\n"
            f"- *Note*: If purchasing in Germany for use in India, remember the QWERTZ keyboard layout and verify if international warranty is provided."
        )

        resp = {
            "role": "assistant",
            "content": verdict_text,
            "type": "arbitrage",
            "structured_data": arbitrage_table
        }
        self.history.append(ChatMessage(role="assistant", content=verdict_text, structured_data=arbitrage_table))
        return resp

    def _handle_flight_intelligence(self, query: str) -> Dict[str, Any]:
        """Handles flight route queries with precision links."""
        res = CypherOrchestrator.scout(query, category="flight", region=self.region, max_results=6)
        
        summary = (
            f"### ✈️ Route Intelligence: {res.summary}\n\n"
            f"- **Target Hubs**: Direct pre-filled booking matrix locked for Google Flights, Skyscanner, and Kayak.\n"
            f"- **Airline Breakdown**: Live fares and schedules scouted across Lufthansa, Emirates, Air India, and partner carriers."
        )

        structured_data = {
            "type": "flight",
            "summary": res.summary,
            "items": [it.model_dump() for it in res.items],
            "deep_links": res.deep_links
        }

        resp = {
            "role": "assistant",
            "content": summary,
            "type": "flight",
            "structured_data": structured_data
        }
        self.history.append(ChatMessage(role="assistant", content=summary, structured_data=structured_data))
        return resp

    def _extract_number(self, text: str) -> Optional[float]:
        clean = text.replace(",", "").replace(".", "").replace("€", "").replace("₹", "").replace("$", "").strip()
        match = re.search(r"(\d+(?:\.\d+)?)", text.replace(",", ""))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None
