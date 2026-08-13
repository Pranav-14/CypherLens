"""
Central Intelligence Orchestrator for CypherLens.
Routes queries to the optimal lens or combines multi-channel intelligence.
"""

import time
from typing import Optional
from cypherlens.engines.base import LensResponse
from cypherlens.engines.query_parser import QueryParser
from cypherlens.engines.amazon_lens import AmazonLens
from cypherlens.engines.flight_lens import FlightLens
from cypherlens.engines.tech_lens import TechLens
from cypherlens.engines.general_lens import GeneralLens


class CypherOrchestrator:
    @staticmethod
    def scout(query: str, category: Optional[str] = None, max_results: int = 8) -> LensResponse:
        start_time = time.time()
        
        # 1. Determine Category
        target_category = category
        if not target_category or target_category == "auto":
            target_category = QueryParser.classify_intent(query)
            
        target_category = target_category.lower()

        # 2. Dispatch to designated lens
        if target_category == "flight":
            response = FlightLens.search(query, max_results=max_results)
        elif target_category == "amazon":
            response = AmazonLens.search(query, max_results=max_results)
        elif target_category == "tech":
            response = TechLens.search(query, max_results=max_results)
        else:
            response = GeneralLens.search(query, max_results=max_results)

        # 3. Calculate execution latency
        elapsed = (time.time() - start_time) * 1000
        response.execution_time_ms = round(elapsed, 2)
        response.detected_category = target_category
        
        return response
