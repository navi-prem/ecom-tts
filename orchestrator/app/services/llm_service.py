import os
from typing import Dict, Any, Optional
import logging
import httpx

logger = logging.getLogger(__name__)


class LLMService:
    """LLM Service using Ollama (local LLM) for query generation and scoring."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama API URL (default: http://localhost:11434)
            model: Ollama model name (default: llama3.2 - fast and good for this use case)
                   Other options: mistral, phi3, gemma2, etc.
        """
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)
        
        logger.info(f"Initialized Ollama client: {model} at {base_url}")
    
    async def _generate(self, prompt: str) -> str:
        """Generate text using Ollama."""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise RuntimeError(f"Ollama failed: {e}")
    
    async def generate_cypher(self, user_query: str) -> str:
        """Generate Cypher query from natural language using Ollama."""
        prompt = f"""You are a Cypher query generator for Neo4j.

Database Schema:
- Node: Product with properties: id, name, brand, color, price, original_price, description, tags (list), category (object with main_category, subcategory, specific_type)
- Full-text index: 'productSearch' on [p.name, p.description, p.brand]

Rules:
1. Use full-text search: CALL db.index.fulltext.queryNodes('productSearch', '<search_terms>') YIELD node RETURN node LIMIT 10
2. For brand/color filters, add WHERE clauses after the fulltext call
3. For price ranges, use WHERE node.price <= <amount> or node.price >= <amount>
4. Always use the fulltext index as the starting point for text search
5. Return the product node as 'node' (not 'p')
6. Return ONLY the Cypher query, no explanations or markdown

Examples:
- "red nike shoes under $100" -> CALL db.index.fulltext.queryNodes('productSearch', 'nike shoes') YIELD node WHERE node.color = 'Red' AND node.price <= 100 RETURN node LIMIT 10
- "apple laptop" -> CALL db.index.fulltext.queryNodes('productSearch', 'apple laptop') YIELD node RETURN node LIMIT 10
- "samsung phone blue" -> CALL db.index.fulltext.queryNodes('productSearch', 'samsung phone') YIELD node WHERE node.color = 'Blue' RETURN node LIMIT 10
- "macbook pro under $3000" -> CALL db.index.fulltext.queryNodes('productSearch', 'macbook pro') YIELD node WHERE node.price <= 3000 RETURN node LIMIT 10

Convert to Cypher: {user_query}

Cypher query:"""

        try:
            cypher = await self._generate(prompt)
            
            # Clean up any markdown code blocks
            if cypher.startswith("```"):
                lines = cypher.split("\n")
                if len(lines) > 2:
                    cypher = "\n".join(lines[1:-1])
                else:
                    cypher = cypher.replace("```cypher", "").replace("```", "").strip()
            
            logger.info(f"Generated Cypher: {cypher}")
            return cypher
            
        except Exception as e:
            logger.error(f"Failed to generate Cypher: {e}")
            # Fallback to simple query
            return f"CALL db.index.fulltext.queryNodes('productSearch', '{user_query}') YIELD node RETURN node LIMIT 10"
    
    async def generate_search_terms(self, user_query: str) -> str:
        """Generate optimized search terms for semantic search using Ollama."""
        prompt = f"""Extract the core product search terms from the user query.
Remove filler words, keep only important keywords for semantic similarity search.

Examples:
- "I want red nike running shoes under $100" -> red nike running shoes
- "Looking for a comfortable leather jacket" -> comfortable leather jacket
- "Apple MacBook Pro 16 inch under $2000" -> Apple MacBook Pro
- "samsung galaxy phone blue" -> samsung galaxy phone
- "kitchen mixer stainless steel" -> kitchen mixer stainless steel

Query: {user_query}

Search terms (just the cleaned terms, nothing else):"""

        try:
            search_terms = await self._generate(prompt)
            logger.info(f"Generated search terms: {search_terms}")
            return search_terms
            
        except Exception as e:
            logger.error(f"Failed to generate search terms: {e}")
            # Fallback to original query
            return user_query
    
    async def score_relevance(self, product: Dict[str, Any], user_query: str) -> float:
        """Score how relevant a product is to the user query using Ollama."""
        product_summary = f"""
Name: {product.get('name', 'N/A')}
Brand: {product.get('brand', 'N/A')}
Color: {product.get('color', 'N/A')}
Price: ${product.get('price', 0)}
Category: {product.get('category', {}).get('specific_type', 'N/A') if product.get('category') else 'N/A'}
Description: {product.get('description', 'N/A')[:100]}...
Tags: {', '.join(product.get('tags', []))}
"""

        prompt = f"""Rate how well this product matches the user's search query.

Rate from 0.0 to 1.0 where:
- 1.0 = Perfect match (exactly what user wants)
- 0.7-0.9 = Good match (meets most criteria)
- 0.4-0.6 = Partial match (some criteria match)
- 0.1-0.3 = Weak match (few criteria match)
- 0.0 = No match

Consider: brand, color, product type, price, description, category, tags.

User query: {user_query}

Product:{product_summary}

Return ONLY a number between 0.0 and 1.0, no explanation.

Relevance score:"""

        try:
            score_text = await self._generate(prompt)
            
            # Extract number from response
            import re
            score_match = re.search(r'(\d+\.?\d*)', score_text)
            if score_match:
                score = float(score_match.group(1))
                score = max(0.0, min(1.0, score))  # Clamp between 0 and 1
                return score
            else:
                logger.warning(f"Could not parse score from: {score_text}")
                return 0.5
            
        except Exception as e:
            logger.error(f"Failed to score relevance: {e}")
            return 0.5
    
    async def close(self):
        """Cleanup"""
        await self.client.aclose()
