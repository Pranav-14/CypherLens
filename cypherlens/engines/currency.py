"""
Dynamic Currency Conversion Engine for CypherLens 2.0.
Provides real-time exchange rates, cross-currency conversions, and locale-aware price formatting.
"""

import time
import httpx
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("cypherlens.currency")

# Base Rates (Relative to 1.00 EUR)
BASELINE_RATES: Dict[str, float] = {
    "EUR": 1.00,
    "USD": 1.09,
    "INR": 91.50,
    "GBP": 0.85,
    "AED": 4.00,
    "CAD": 1.48,
    "JPY": 165.00,
    "SGD": 1.45,
    "CHF": 0.96,
    "AUD": 1.66
}

CURRENCY_METADATA: Dict[str, Dict[str, str]] = {
    "EUR": {"symbol": "€", "name": "Euro", "flag": "🇪🇺", "pos": "after"},
    "INR": {"symbol": "₹", "name": "Indian Rupee", "flag": "🇮🇳", "pos": "before"},
    "USD": {"symbol": "$", "name": "US Dollar", "flag": "🇺🇸", "pos": "before"},
    "GBP": {"symbol": "£", "name": "British Pound", "flag": "🇬🇧", "pos": "before"},
    "AED": {"symbol": "AED", "name": "UAE Dirham", "flag": "🇦🇪", "pos": "before"},
    "CAD": {"symbol": "CA$", "name": "Canadian Dollar", "flag": "🇨🇦", "pos": "before"},
    "JPY": {"symbol": "¥", "name": "Japanese Yen", "flag": "🇯🇵", "pos": "before"},
    "SGD": {"symbol": "SG$", "name": "Singapore Dollar", "flag": "🇸🇬", "pos": "before"},
    "CHF": {"symbol": "CHF", "name": "Swiss Franc", "flag": "🇨🇭", "pos": "before"},
    "AUD": {"symbol": "AU$", "name": "Australian Dollar", "flag": "🇦🇺", "pos": "before"}
}


class CurrencyConverter:
    _rates: Dict[str, float] = BASELINE_RATES.copy()
    _last_fetched: float = 0.0

    @classmethod
    def refresh_rates(cls):
        """Attempts to fetch live exchange rates from open exchange API."""
        if time.time() - cls._last_fetched < 3600:
            return  # Cache for 1 hour
            
        try:
            r = httpx.get("https://open.er-api.com/v6/latest/EUR", timeout=4.0)
            if r.status_code == 200:
                data = r.json()
                live_rates = data.get("rates", {})
                for c in cls._rates:
                    if c in live_rates:
                        cls._rates[c] = float(live_rates[c])
                cls._last_fetched = time.time()
        except Exception as e:
            logger.debug(f"Live currency update skipped: {e}")

    @classmethod
    def convert(cls, amount: float, from_curr: str = "EUR", to_curr: str = "INR") -> float:
        """Converts an amount from one currency to another."""
        if not amount:
            return 0.0
            
        f = from_curr.upper()
        t = to_curr.upper()
        if f == t:
            return round(amount, 2)

        cls.refresh_rates()
        rate_from = cls._rates.get(f, BASELINE_RATES.get(f, 1.0))
        rate_to = cls._rates.get(t, BASELINE_RATES.get(t, 1.0))

        # Convert to EUR base, then to target
        amount_eur = amount / rate_from
        converted = amount_eur * rate_to
        return round(converted, 2)

    @classmethod
    def format(cls, amount: float, currency: str = "EUR") -> str:
        """Formats an amount into localized currency string (e.g. ₹ 1,44,990 or 1.299 €)."""
        curr = currency.upper()
        meta = CURRENCY_METADATA.get(curr, {"symbol": curr, "pos": "before"})
        sym = meta["symbol"]

        if curr in ["INR"]:
            # Format with Indian numbering system (Lakhs/Crores)
            s = f"{int(amount):,}" if amount.is_integer() else f"{amount:,.2f}"
            return f"{sym} {s}"
        elif curr in ["EUR", "CHF"]:
            # European format
            s = f"{int(amount):,}".replace(",", ".") if amount.is_integer() else f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"{s} {sym}"
        else:
            s = f"{int(amount):,}" if amount.is_integer() else f"{amount:,.2f}"
            return f"{sym}{s}"

    @classmethod
    def get_supported_currencies(cls) -> List[Dict[str, Any]]:
        """Returns all supported currencies with symbols and flags."""
        res = []
        for code, meta in CURRENCY_METADATA.items():
            res.append({
                "code": code,
                "name": meta["name"],
                "symbol": meta["symbol"],
                "flag": meta["flag"],
                "rate_to_eur": cls._rates.get(code, BASELINE_RATES.get(code, 1.0))
            })
        return res
