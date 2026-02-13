from typing import List, Dict, Any, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance, VectorParams, PointStruct, 
    Filter, FieldCondition, MatchValue,
    ScoredPoint, Range, HasIdCondition
)
import logging
import time
import hashlib
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _generate_point_id(product_id: str) -> str:
    """Generate a valid UUID from product_id string."""
    hash_bytes = hashlib.md5(product_id.encode()).digest()
    return str(uuid.UUID(bytes=hash_bytes[:16]))


class VectorStore:
    def __init__(
        self, 
        collection_name: str = "products",
        qdrant_url: str = "http://localhost:6333",
        vector_size: int = 384,
        batch_size: int = 500
    ):
        self.collection_name = collection_name
        self.qdrant_url = qdrant_url
        self.vector_size = vector_size
        self.batch_size = batch_size
        self.client: Optional[QdrantClient] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Qdrant client with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.client = QdrantClient(url=self.qdrant_url)
                self._ensure_collection_exists()
                logger.info(f"Connected to Qdrant at {self.qdrant_url}")
                return
            except Exception as e:
                logger.error(f"Failed to connect to Qdrant (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist."""
        if self.client is None:
            raise RuntimeError("Client not initialized")
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection {self.collection_name} created successfully")
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise
    
    def upsert_products(
        self, 
        points: List[Dict[str, Any]], 
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Insert or update products in batches with error handling."""
        if self.client is None:
            raise RuntimeError("Client not initialized")
        
        if not points:
            return {"inserted": 0, "errors": ["No products to insert"]}
        
        batch_size = batch_size or self.batch_size
        total_inserted = 0
        errors = []
        
        # Process in batches
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Convert to PointStruct
                    point_structs = [
                        PointStruct(
                            id=point["id"],
                            vector=point["vector"],
                            payload=point["payload"]
                        )
                        for point in batch
                    ]
                    
                    # Upsert batch
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=point_structs,
                        wait=True
                    )
                    total_inserted += len(batch)
                    logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} products")
                    break
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    error_msg = f"Batch {i//batch_size + 1} failed after {max_retries} attempts: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
        
        return {
            "inserted": total_inserted,
            "total": len(points),
            "errors": errors
        }
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        min_score: float = 0.3
    ) -> List[ScoredPoint]:
        """Search for similar products with optional filters and score threshold."""
        if self.client is None:
            raise RuntimeError("Client not initialized")
        try:
            qdrant_filter = self._build_filter(filters) if filters else None
            
            # Use query_points for vector search - query parameter takes the vector directly
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                query_filter=qdrant_filter,
                with_payload=True,
                with_vectors=False,
                score_threshold=min_score  # Filter out low similarity results
            )
            
            # Convert results to ScoredPoint format
            scored_points = []
            for point in results.points:
                version = getattr(point, 'version', 0)
                if version is None:
                    version = 0
                scored_points.append(ScoredPoint(
                    id=str(point.id),
                    score=float(point.score) if hasattr(point, 'score') else 0.0,
                    payload=point.payload if hasattr(point, 'payload') else None,
                    version=version
                ))
            
            return scored_points
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def _build_filter(self, filters: Dict[str, Any]) -> Optional[Filter]:
        """Build Qdrant filter from dict."""
        conditions = []
        
        if "brand" in filters:
            conditions.append(
                FieldCondition(
                    key="brand",
                    match=MatchValue(value=filters["brand"])
                )
            )
        
        if "category" in filters:
            conditions.append(
                FieldCondition(
                    key="category_main",
                    match=MatchValue(value=filters["category"])
                )
            )
        
        if "gender" in filters:
            conditions.append(
                FieldCondition(
                    key="gender",
                    match=MatchValue(value=filters["gender"])
                )
            )
        
        if "max_price" in filters:
            conditions.append(
                FieldCondition(
                    key="price",
                    range=Range(lte=filters["max_price"])
                )
            )
        
        return Filter(must=conditions) if conditions else None
    
    def delete_product(self, product_id: str) -> bool:
        """Delete a product by ID."""
        if self.client is None:
            raise RuntimeError("Client not initialized")
        try:
            # Convert to UUID if it's a string product_id
            point_id = _generate_point_id(product_id)
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[point_id]
            )
            logger.info(f"Deleted product: {product_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete product {product_id}: {e}")
            return False
    
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get a single product by ID."""
        if self.client is None:
            raise RuntimeError("Client not initialized")
        try:
            # Convert to UUID if it's a string product_id
            point_id = _generate_point_id(product_id)
            results = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id],
                with_payload=True,
                with_vectors=False
            )
            if results:
                return {
                    "id": str(results[0].id),
                    "payload": results[0].payload
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {e}")
            return None
    
    def count(self) -> int:
        """Get total number of products."""
        if self.client is None:
            raise RuntimeError("Client not initialized")
        try:
            result = self.client.count(collection_name=self.collection_name)
            return result.count
        except Exception as e:
            logger.error(f"Failed to count products: {e}")
            return 0
    
    def delete_collection(self):
        """Delete entire collection (use with caution)."""
        if self.client is None:
            raise RuntimeError("Client not initialized")
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")


# Singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create singleton vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def reset_vector_store():
    """Reset singleton (useful for testing)."""
    global _vector_store
    _vector_store = None
