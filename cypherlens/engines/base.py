"""
Base data models and interfaces for CypherLens intelligence lenses.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    title: str
    url: str
    source: str = "Web"
    category: str = "general"  # "amazon", "flight", "tech", "general"
    price: Optional[str] = None
    price_num: Optional[float] = None
    rating: Optional[str] = None
    reviews_count: Optional[str] = None
    badge: Optional[str] = None
    image_url: Optional[str] = None
    snippet: str = ""
    specs: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


class LensResponse(BaseModel):
    query: str
    detected_category: str
    region: str = "de"
    region_name: str = "Germany & EU"
    currency: str = "EUR"
    summary: str = ""
    items: List[SearchResultItem] = Field(default_factory=list)
    deep_links: List[Dict[str, str]] = Field(default_factory=list)
    execution_time_ms: float = 0.0
