from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import logging

from app.models.schemas import (
    SearchRequest, SearchResponse, SearchResultItem,
    ProductBatchRequest, InsertResponse, DeleteResponse, HealthResponse
)
from app.services.embedding import get_embedding_service, EmbeddingService
from app.services.vector_store import get_vector_store, VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Product Vector Search API",
    description="Semantic search for e-commerce products using Qdrant",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection
def get_embedding_svc() -> EmbeddingService:
    return get_embedding_service()


def get_vector_store_svc() -> VectorStore:
    return get_vector_store()


@app.get("/", tags=["Health"])
async def root():
    return {"message": "Product Vector Search API", "version": "1.0.0"}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(store: VectorStore = Depends(get_vector_store_svc)):
    """Check service health and Qdrant connection."""
    try:
        count = store.count()
        return HealthResponse(
            status="healthy",
            products_count=count,
            qdrant_connected=True
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            products_count=0,
            qdrant_connected=False
        )


@app.post("/api/v1/products", response_model=InsertResponse, tags=["Products"])
async def add_product(
    product: Dict[str, Any],
    embedding_svc: EmbeddingService = Depends(get_embedding_svc),
    store: VectorStore = Depends(get_vector_store_svc)
):
    """Add a single product to the vector store."""
    try:
        # Validate required fields
        if "id" not in product:
            raise HTTPException(status_code=400, detail="Product must have an 'id' field")
        
        # Generate embedding
        points = embedding_svc.embed_products([product])
        
        if not points:
            raise HTTPException(status_code=400, detail="Failed to generate embedding for product")
        
        # Insert to Qdrant
        result = store.upsert_products(points)
        
        return InsertResponse(
            success=len(result["errors"]) == 0,
            inserted_count=result["inserted"],
            total=1,
            message=f"Successfully added product: {product['id']}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add product: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add product: {str(e)}")


@app.post("/api/v1/products/batch", response_model=InsertResponse, tags=["Products"])
async def add_products_batch(
    request: ProductBatchRequest,
    embedding_svc: EmbeddingService = Depends(get_embedding_svc),
    store: VectorStore = Depends(get_vector_store_svc)
):
    """Add multiple products in batch (recommended for large imports)."""
    try:
        if not request.products:
            raise HTTPException(status_code=400, detail="No products provided")
        
        # Validate all products have IDs
        for i, product in enumerate(request.products):
            if "id" not in product:
                raise HTTPException(status_code=400, detail=f"Product at index {i} missing 'id' field")
        
        logger.info(f"Processing {len(request.products)} products for batch insert")
        
        # Generate embeddings in batch (efficient!)
        points = embedding_svc.embed_products(request.products)
        
        if not points:
            raise HTTPException(status_code=400, detail="Failed to generate embeddings")
        
        # Insert to Qdrant with batching
        result = store.upsert_products(points)
        
        return InsertResponse(
            success=len(result["errors"]) == 0,
            inserted_count=result["inserted"],
            total=len(request.products),
            message=f"Successfully inserted {result['inserted']}/{len(request.products)} products"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to batch insert products: {e}")
        raise HTTPException(status_code=500, detail=f"Batch insert failed: {str(e)}")


@app.delete("/api/v1/products/{product_id}", response_model=DeleteResponse, tags=["Products"])
async def delete_product(
    product_id: str,
    store: VectorStore = Depends(get_vector_store_svc)
):
    """Delete a product from the vector store."""
    try:
        success = store.delete_product(product_id)
        if success:
            return DeleteResponse(success=True, message=f"Product {product_id} deleted")
        else:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete product: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")


@app.post("/api/v1/search", response_model=SearchResponse, tags=["Search"])
async def search_products(
    request: SearchRequest,
    embedding_svc: EmbeddingService = Depends(get_embedding_svc),
    store: VectorStore = Depends(get_vector_store_svc)
):
    """Search for products using semantic similarity."""
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        # Generate query embedding
        query_vector = embedding_svc.embed_query(request.query)
        
        # Search in Qdrant
        results = store.search(
            query_vector=query_vector,
            limit=request.limit,
            filters=request.filters,
            min_score=request.min_score
        )
        
        # Format results
        search_results = []
        for point in results:
            payload = point.payload or {}
            search_results.append(SearchResultItem(
                product_id=payload.get("product_id", str(point.id)),
                score=point.score,
                name=payload.get("name", ""),
                brand=payload.get("brand", ""),
                price=payload.get("price", 0.0)
            ))
        
        return SearchResponse(
            query=request.query,
            results=search_results,
            total_found=len(search_results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/v1/products/{product_id}", tags=["Products"])
async def get_product(
    product_id: str,
    store: VectorStore = Depends(get_vector_store_svc)
):
    """Get a product by ID."""
    try:
        product = store.get_product(product_id)
        if product:
            return product
        else:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get product: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
