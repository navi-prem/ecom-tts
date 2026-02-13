from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None
    min_score: float = 0.3  # Minimum similarity score (0-1), default 0.3


class ProductBatchRequest(BaseModel):
    products: List[Dict[str, Any]]


class SearchResultItem(BaseModel):
    product_id: str
    score: float
    name: str
    brand: str
    price: float


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    total_found: int


class InsertResponse(BaseModel):
    success: bool
    inserted_count: int
    total: int
    message: str


class DeleteResponse(BaseModel):
    success: bool
    message: str


class HealthResponse(BaseModel):
    status: str
    products_count: int
    qdrant_connected: bool
