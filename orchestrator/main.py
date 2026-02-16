from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import logging
import os
import asyncio

from app.models.schemas import (
    ProductQueryRequest, ProductQueryResponse,
    RecommendationResult, HealthResponse
)
from app.clients.semantic_client import SemanticEngineClient
from app.clients.graph_client import GraphServiceClient
from app.services.llm_service import LLMService
from app.services.recommendation_service import RecommendationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Product Search Orchestrator",
    description="Orchestrates semantic and graph search with LLM-powered query understanding",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SEMANTIC_ENGINE_URL = os.getenv("SEMANTIC_ENGINE_URL", "http://localhost:8000")
GRAPH_SERVICE_TARGET = os.getenv("GRAPH_SERVICE_TARGET", "localhost:50051")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def get_semantic_client():
    return SemanticEngineClient(base_url=SEMANTIC_ENGINE_URL)


def get_graph_client():
    client = GraphServiceClient(target=GRAPH_SERVICE_TARGET)
    client.connect()
    return client


def get_llm_service():
    return LLMService(api_key=GOOGLE_API_KEY)


def get_recommendation_service():
    return RecommendationService(
        semantic_weight=0.5,
        graph_weight=0.5,
        diversity_boost=0.05
    )


@app.get("/", tags=["Health"])
async def root():
    return {"message": "Product Search Orchestrator", "version": "1.0.0"}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(
    semantic_client: SemanticEngineClient = Depends(get_semantic_client),
    graph_client: GraphServiceClient = Depends(get_graph_client)
):
    try:
        semantic_healthy = await semantic_client.health_check()
    except Exception as e:
        logger.error(f"Semantic engine health check error: {e}")
        semantic_healthy = False
    
    try:
        graph_healthy = graph_client.health_check()
    except Exception as e:
        logger.error(f"Graph service health check error: {e}")
        graph_healthy = False
    
    await semantic_client.close()
    graph_client.close()
    
    status = "healthy" if (semantic_healthy and graph_healthy) else "degraded"
    
    return HealthResponse(
        status=status,
        semantic_engine_connected=semantic_healthy,
        graph_service_connected=graph_healthy
    )


@app.post("/api/v1/search", response_model=ProductQueryResponse, tags=["Search"])
async def search_products(
    request: ProductQueryRequest,
    semantic_client: SemanticEngineClient = Depends(get_semantic_client),
    graph_client: GraphServiceClient = Depends(get_graph_client),
    llm_service: LLMService = Depends(get_llm_service),
    recommendation_service: RecommendationService = Depends(get_recommendation_service)
):
    try:
        logger.info(f"Processing search query: {request.query}")
        
        # Step 1: Generate both queries in parallel via LLM
        cypher_task = llm_service.generate_cypher(request.query)
        terms_task = llm_service.generate_search_terms(request.query)
        
        cypher_query, search_terms = await asyncio.gather(cypher_task, terms_task)
        logger.info(f"Generated Cypher: {cypher_query}")
        logger.info(f"Generated search terms: {search_terms}")
        
        # Step 2: Execute searches (semantic is async, graph is sync)
        semantic_results = await semantic_client.search(
            query=search_terms,
            limit=request.limit * 2,
            min_score=request.min_semantic_score
        )
        
        graph_results = graph_client.search_products(cypher_query)
        
        logger.info(f"Semantic search returned {len(semantic_results)} results")
        logger.info(f"Graph search returned {len(graph_results)} results")
        
        # Step 3: Combine results with LLM scoring
        recommendations = await recommendation_service.combine_results(
            semantic_results=semantic_results,
            graph_results=graph_results,
            query=request.query,
            llm_service=llm_service,
            limit=request.limit
        )
        logger.info(f"Generated {len(recommendations)} recommendations")
        
        await semantic_client.close()
        graph_client.close()
        
        return ProductQueryResponse(
            query=request.query,
            cypher_query=cypher_query,
            search_terms=search_terms,
            semantic_results_count=len(semantic_results),
            graph_results_count=len(graph_results),
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        await semantic_client.close()
        graph_client.close()
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/api/v1/products", tags=["Products"])
async def create_product(
    product: Dict[str, Any],
    semantic_client: SemanticEngineClient = Depends(get_semantic_client),
    graph_client: GraphServiceClient = Depends(get_graph_client)
):
    try:
        if "id" not in product:
            raise HTTPException(status_code=400, detail="Product must have an 'id' field")
        
        semantic_success = await semantic_client.add_product(product)
        graph_id = graph_client.create_product(product)
        
        await semantic_client.close()
        graph_client.close()
        
        return {
            "success": semantic_success and graph_id is not None,
            "product_id": product["id"],
            "semantic_inserted": semantic_success,
            "graph_inserted": graph_id is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create product: {e}")
        await semantic_client.close()
        graph_client.close()
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")


@app.post("/api/v1/products/batch", tags=["Products"])
async def create_products_batch(
    products: List[Dict[str, Any]],
    semantic_client: SemanticEngineClient = Depends(get_semantic_client),
    graph_client: GraphServiceClient = Depends(get_graph_client)
):
    try:
        for i, product in enumerate(products):
            if "id" not in product:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Product at index {i} missing 'id' field"
                )
        
        semantic_success = await semantic_client.add_products_batch(products)
        
        graph_ids = []
        for product in products:
            graph_id = graph_client.create_product(product)
            graph_ids.append(graph_id)
        
        await semantic_client.close()
        graph_client.close()
        
        graph_success_count = sum(1 for gid in graph_ids if gid is not None)
        
        return {
            "success": semantic_success and graph_success_count == len(products),
            "total": len(products),
            "semantic_inserted": semantic_success,
            "graph_inserted_count": graph_success_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to batch insert products: {e}")
        await semantic_client.close()
        graph_client.close()
        raise HTTPException(status_code=500, detail=f"Batch insert failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6969)
