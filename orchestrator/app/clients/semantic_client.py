import httpx
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SemanticEngineClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Semantic engine health check failed: {e}")
            return False
    
    async def search(self, query: str, limit: int = 10, 
                     filters: Optional[Dict[str, Any]] = None,
                     min_score: float = 0.3) -> List[Dict[str, Any]]:
        try:
            payload = {
                "query": query,
                "limit": limit,
                "min_score": min_score
            }
            if filters:
                payload["filters"] = filters
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/search",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def add_product(self, product: Dict[str, Any]) -> bool:
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/products",
                json=product
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to add product to semantic engine: {e}")
            return False
    
    async def add_products_batch(self, products: List[Dict[str, Any]]) -> bool:
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/products/batch",
                json={"products": products}
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to add products batch to semantic engine: {e}")
            return False
    
    async def close(self):
        await self.client.aclose()
