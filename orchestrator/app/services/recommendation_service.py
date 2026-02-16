from typing import List, Dict, Any
import logging
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class RecommendationService:
    def __init__(
        self,
        semantic_weight: float = 0.5,
        graph_weight: float = 0.5,
        diversity_boost: float = 0.05
    ):
        self.semantic_weight = semantic_weight
        self.graph_weight = graph_weight
        self.diversity_boost = diversity_boost
    
    async def combine_results(
        self,
        semantic_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]],
        query: str,
        llm_service,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Combine results from both services using LLM scoring."""
        # Use regular dict instead of defaultdict to avoid type issues
        product_scores: Dict[str, Dict[str, Any]] = {}
        
        # Helper function to get or create product entry
        def get_product_entry(product_id: str) -> Dict[str, Any]:
            if product_id not in product_scores:
                product_scores[product_id] = {
                    "semantic_score": 0.0,
                    "graph_score": 0.0,
                    "data": None,
                    "sources": set()
                }
            return product_scores[product_id]
        
        # Process semantic results
        for result in semantic_results:
            product_id = result.get("product_id", result.get("id"))
            if product_id:
                entry = get_product_entry(product_id)
                entry["semantic_score"] = result.get("score", 0.0)
                entry["sources"].add("semantic")
                if entry["data"] is None:
                    entry["data"] = result
        
        # Process graph results
        for result in graph_results:
            product_id = result.get("id", result.get("product_id"))
            if product_id:
                entry = get_product_entry(product_id)
                entry["sources"].add("graph")
                if entry["data"] is None:
                    entry["data"] = result
                else:
                    entry["data"].update(result)
        
        # Score products with LLM (Ollama - no rate limits)
        scored_products = []
        product_ids = list(product_scores.keys())
        
        for product_id in product_ids:
            scores = product_scores[product_id]
            
            try:
                # Score with LLM (no delays needed for Ollama)
                graph_score_value = await llm_service.score_relevance(scores["data"], query)
            except Exception as e:
                logger.warning(f"LLM scoring failed for {product_id}: {e}")
                graph_score_value = 0.5  # Default score
            
            scores["graph_score"] = graph_score_value
            
            # Calculate combined score
            combined_score = self._calculate_combined_score(
                float(scores["semantic_score"]),
                graph_score_value,
                scores["sources"]
            )
            
            scored_products.append({
                "product_id": product_id,
                "semantic_score": scores["semantic_score"],
                "graph_score": graph_score_value,
                "combined_score": combined_score,
                "data": scores["data"],
                "sources": list(scores["sources"])
            })
        
        # Sort by combined score
        scored_products.sort(key=lambda x: x["combined_score"], reverse=True)
        
        # Build final results
        final_results = []
        for item in scored_products[:limit]:
            result = {
                "product_id": item["product_id"],
                "name": item["data"].get("name", ""),
                "brand": item["data"].get("brand", ""),
                "price": item["data"].get("price", 0.0),
                "semantic_score": round(item["semantic_score"], 4),
                "graph_score": round(item["graph_score"], 4),
                "combined_score": round(item["combined_score"], 4),
                "description": item["data"].get("description", ""),
                "color": item["data"].get("color", ""),
                "category": item["data"].get("category"),
                "sources": item["sources"]
            }
            final_results.append(result)
        
        return final_results
    
    def _calculate_combined_score(
        self,
        semantic_score: float,
        graph_score: float,
        sources: set
    ) -> float:
        """Calculate combined score with diversity boost."""
        has_semantic = "semantic" in sources
        has_graph = "graph" in sources
        
        if has_semantic and has_graph:
            # Product found in both - boost score
            combined = (
                self.semantic_weight * semantic_score +
                self.graph_weight * graph_score
            )
            boost = self.diversity_boost
        elif has_semantic:
            # Only semantic
            combined = semantic_score
            boost = 0
        elif has_graph:
            # Only graph
            combined = graph_score
            boost = 0
        else:
            combined = 0
            boost = 0
        
        return min(combined + boost, 1.0)
