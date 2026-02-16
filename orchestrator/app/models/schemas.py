from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ProductCategory(BaseModel):
    main_category: str
    subcategory: str
    specific_type: str


class ProductSize(BaseModel):
    size: str
    stock: int
    in_stock: bool
    variants: List[str]
    sku: str


class Product(BaseModel):
    id: str
    name: str
    brand: str
    category: ProductCategory
    color: str
    price: float
    original_price: float
    sizes: List[ProductSize]
    tags: List[str]
    attributes: Dict[str, str]
    description: str
    images: List[str]


class SemanticSearchResult(BaseModel):
    product_id: str
    score: float
    name: str
    brand: str
    price: float


class GraphSearchResult(BaseModel):
    product_id: str
    name: str
    brand: str
    price: float
    category: Optional[ProductCategory] = None
    color: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class RecommendationResult(BaseModel):
    product_id: str
    name: str
    brand: str
    price: float
    semantic_score: float
    graph_score: float
    combined_score: float
    description: Optional[str] = None
    color: Optional[str] = None
    category: Optional[ProductCategory] = None


class ProductQueryRequest(BaseModel):
    query: str
    limit: int = 10
    min_semantic_score: float = 0.3


class ProductQueryResponse(BaseModel):
    query: str
    cypher_query: Optional[str] = None
    search_terms: Optional[str] = None
    semantic_results_count: int
    graph_results_count: int
    recommendations: List[RecommendationResult]


class HealthResponse(BaseModel):
    status: str
    semantic_engine_connected: bool
    graph_service_connected: bool
