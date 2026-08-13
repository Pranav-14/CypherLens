"""
Natural Language Date Parser for CypherLens Flight and Travel Queries.
Translates expressions like 'december 12th to january 17th' into standard ISO dates.
"""

import re
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sept": 9, "sep": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12
}


class DateParser:
    @staticmethod
    def parse_flight_dates(query: str, reference_date: Optional[date] = None) -> Dict[str, Any]:
        ref = reference_date or date.today()
        current_year = ref.year
        q_lower = query.lower()

        trip_type = "oneway" if ("one way" in q_lower or "oneway" in q_lower or "one-way" in q_lower) else "roundtrip"

        res = {
            "outbound_iso": None,
            "inbound_iso": None,
            "outbound_sky": None,
            "inbound_sky": None,
            "trip_type": trip_type,
            "raw_date_str": ""
        }

        # 1. Match two dates: "<Month1> <Day1> [to/through/-] <Month2> <Day2>"
        pattern_two_months = re.search(
            r"([a-z]+)\s*(\d{1,2})(?:st|nd|rd|th)?\s*(?:to|through|until|-|–)\s*([a-z]+)\s*(\d{1,2})(?:st|nd|rd|th)?",
            q_lower
        )
        if pattern_two_months:
            m1_str, d1_str, m2_str, d2_str = pattern_two_months.groups()
            if m1_str in MONTH_MAP and m2_str in MONTH_MAP:
                m1 = MONTH_MAP[m1_str]
                d1 = int(d1_str)
                m2 = MONTH_MAP[m2_str]
                d2 = int(d2_str)

                y1 = current_year
                if m1 < ref.month:
                    y1 = current_year + 1

                y2 = y1
                if m2 < m1:
                    y2 = y1 + 1  # Rollover to next year

                try:
                    dt1 = date(y1, m1, d1)
                    dt2 = date(y2, m2, d2)
                    res["outbound_iso"] = dt1.strftime("%Y-%m-%d")
                    res["inbound_iso"] = dt2.strftime("%Y-%m-%d")
                    res["outbound_sky"] = dt1.strftime("%y%m%d")
                    res["inbound_sky"] = dt2.strftime("%y%m%d")
                    res["raw_date_str"] = f"{dt1.strftime('%b %d, %Y')} to {dt2.strftime('%b %d, %Y')}"
                    return res
                except ValueError:
                    pass

        # 2. Match two days in same month: "<Month> <Day1> [to/-] <Day2>"
        pattern_same_month = re.search(
            r"([a-z]+)\s*(\d{1,2})(?:st|nd|rd|th)?\s*(?:to|through|until|-|–)\s*(\d{1,2})(?:st|nd|rd|th)?",
            q_lower
        )
        if pattern_same_month:
            m_str, d1_str, d2_str = pattern_same_month.groups()
            if m_str in MONTH_MAP:
                m = MONTH_MAP[m_str]
                d1 = int(d1_str)
                d2 = int(d2_str)
                y = current_year if m >= ref.month else current_year + 1
                try:
                    dt1 = date(y, m, d1)
                    dt2 = date(y, m, d2)
                    res["outbound_iso"] = dt1.strftime("%Y-%m-%d")
                    res["inbound_iso"] = dt2.strftime("%Y-%m-%d")
                    res["outbound_sky"] = dt1.strftime("%y%m%d")
                    res["inbound_sky"] = dt2.strftime("%y%m%d")
                    res["raw_date_str"] = f"{dt1.strftime('%b %d')} to {dt2.strftime('%b %d, %Y')}"
                    return res
                except ValueError:
                    pass

        # 3. Match single date: "<Month> <Day>"
        pattern_single_date = re.search(r"\b([a-z]+)\s*(\d{1,2})(?:st|nd|rd|th)?\b", q_lower)
        if pattern_single_date:
            m_str, d_str = pattern_single_date.groups()
            if m_str in MONTH_MAP:
                m = MONTH_MAP[m_str]
                d = int(d_str)
                y = current_year if m >= ref.month else current_year + 1
                try:
                    dt1 = date(y, m, d)
                    res["outbound_iso"] = dt1.strftime("%Y-%m-%d")
                    res["outbound_sky"] = dt1.strftime("%y%m%d")
                    
                    if trip_type == "roundtrip":
                        dt2 = dt1 + timedelta(days=7)
                        res["inbound_iso"] = dt2.strftime("%Y-%m-%d")
                        res["inbound_sky"] = dt2.strftime("%y%m%d")
                        res["raw_date_str"] = f"{dt1.strftime('%b %d, %Y')} (7 days)"
                    else:
                        res["raw_date_str"] = dt1.strftime('%b %d, %Y')
                    return res
                except ValueError:
                    pass

        # 4. Relative month
        if "next month" in q_lower:
            next_m = (ref.month % 12) + 1
            next_y = ref.year if next_m > 1 else ref.year + 1
            dt1 = date(next_y, next_m, 10)
            dt2 = date(next_y, next_m, 20)
            res["outbound_iso"] = dt1.strftime("%Y-%m-%d")
            res["inbound_iso"] = dt2.strftime("%Y-%m-%d")
            res["outbound_sky"] = dt1.strftime("%y%m%d")
            res["inbound_sky"] = dt2.strftime("%y%m%d")
            res["raw_date_str"] = f"Next Month ({dt1.strftime('%B %Y')})"
            return res

        for m_name, m_num in MONTH_MAP.items():
            if f"in {m_name}" in q_lower or f"for {m_name}" in q_lower or f"during {m_name}" in q_lower:
                y = current_year if m_num >= ref.month else current_year + 1
                dt1 = date(y, m_num, 10)
                dt2 = date(y, m_num, 20)
                res["outbound_iso"] = dt1.strftime("%Y-%m-%d")
                res["inbound_iso"] = dt2.strftime("%Y-%m-%d")
                res["outbound_sky"] = dt1.strftime("%y%m%d")
                res["inbound_sky"] = dt2.strftime("%y%m%d")
                res["raw_date_str"] = f"{m_name.capitalize()} {y}"
                return res

        # Default fallback
        default_out = ref + timedelta(days=30)
        default_in = default_out + timedelta(days=10)
        res["outbound_iso"] = default_out.strftime("%Y-%m-%d")
        res["inbound_iso"] = default_in.strftime("%Y-%m-%d")
        res["outbound_sky"] = default_out.strftime("%y%m%d")
        res["inbound_sky"] = default_in.strftime("%y%m%d")
        res["raw_date_str"] = "Flexible Dates (Next 30-45 Days)"
        return res
