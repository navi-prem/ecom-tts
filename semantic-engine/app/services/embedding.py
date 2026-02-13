import json
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from functools import lru_cache
import hashlib
import uuid


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        dim = self.model.get_sentence_embedding_dimension()
        self.vector_size: int = dim if dim is not None else 384
    
    def _generate_point_id(self, product_id: str) -> str:
        """Generate a valid UUID from product_id string."""
        # Use MD5 hash to create deterministic UUID from product_id
        hash_bytes = hashlib.md5(product_id.encode()).digest()
        return str(uuid.UUID(bytes=hash_bytes[:16]))
    
    def construct_searchable_text(self, product: Dict[str, Any]) -> str:
        """Construct rich text representation for embedding from product data."""
        parts = []
        
        # Primary searchable content
        parts.append(product.get("name", ""))
        parts.append(product.get("description", ""))
        parts.append(product.get("brand", ""))
        
        # Category hierarchy
        category = product.get("category", {})
        if category:
            parts.append(category.get("main_category", ""))
            parts.append(category.get("subcategory", ""))
            parts.append(category.get("specific_type", ""))
        
        # Tags and attributes
        tags = product.get("tags", [])
        parts.extend(tags)
        
        attributes = product.get("attributes", {})
        for key, value in attributes.items():
            parts.append(f"{key}: {value}")
        
        # Color and gender
        parts.append(product.get("color", ""))
        if "gender" in attributes:
            parts.append(attributes["gender"])
        
        # Join all parts with spaces
        text = " ".join(filter(None, parts))
        return text.strip()
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0 for _ in range(self.vector_size)]
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings for multiple products efficiently."""
        if not products:
            return []
        
        # Construct texts for all products
        texts = []
        valid_indices = []
        
        for i, product in enumerate(products):
            text = self.construct_searchable_text(product)
            if text:
                texts.append(text)
                valid_indices.append(i)
        
        if not texts:
            return []
        
        # Batch encode all texts at once (much faster than one-by-one)
        embeddings = self.model.encode(texts, convert_to_numpy=True, batch_size=32)
        
        # Build result with embeddings
        results = []
        for idx, emb_idx in enumerate(valid_indices):
            product = products[emb_idx]
            # Generate UUID from product_id for Qdrant compatibility
            point_id = self._generate_point_id(product["id"])
            results.append({
                "id": point_id,
                "vector": embeddings[idx].tolist(),
                "payload": self._build_payload(product)
            })
        
        return results
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for search query."""
        return self.embed_text(query)
    
    def _build_payload(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Build searchable payload from product data."""
        return {
            "product_id": product["id"],
            "name": product["name"],
            "brand": product["brand"],
            "category_main": product.get("category", {}).get("main_category"),
            "category_sub": product.get("category", {}).get("subcategory"),
            "category_type": product.get("category", {}).get("specific_type"),
            "color": product["color"],
            "price": product["price"],
            "tags": product["tags"],
            "attributes": product["attributes"],
            "gender": product.get("attributes", {}).get("gender"),
            "searchable_text": self.construct_searchable_text(product)
        }


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """Singleton pattern for embedding service."""
    return EmbeddingService()
