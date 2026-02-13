from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Category(BaseModel):
    main_category: str
    subcategory: str
    specific_type: str


class SizeVariant(BaseModel):
    size: str
    variants: List[str]
    sku: str


class Product(BaseModel):
    id: str = Field(..., alias="id")
    name: str
    brand: str
    category: Category
    color: str
    price: float
    original_price: float
    sizes: List[SizeVariant]
    tags: List[str]
    attributes: Dict[str, str]
    description: str
    images: List[str]

    class Config:
        populate_by_name = True


class ProductSearchResult(BaseModel):
    product_id: str
    score: float
    payload: Dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    results: List[ProductSearchResult]
    total_found: int


class BatchInsertResponse(BaseModel):
    inserted_count: int
    errors: List[str]
