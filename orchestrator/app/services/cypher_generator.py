#!/usr/bin/env python3
"""
LLM-based Cypher Query Generator
Generates Cypher queries directly from natural language using LLM
"""

import json
import os
from typing import Dict, Any, Optional
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class CypherGenerator:
    """Generates Cypher queries from natural language using LLM."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
    
    def generate_cypher(self, user_query: str) -> str:
        """Generate Cypher query from natural language."""
        if not self.client:
            # Fallback: return a basic full-text search query
            return f"CALL db.index.fulltext.queryNodes('productSearch', '{user_query}') YIELD node RETURN node LIMIT 10"
        
        system_prompt = """You are a Cypher query generator for Neo4j. Convert natural language queries into Cypher queries.

Database Schema:
- Node: Product with properties: id, name, brand, color, price, original_price, description, tags (list), category (object with main_category, subcategory, specific_type), sizes (list of objects)
- Full-text index: 'productSearch' on [p.name, p.description, p.brand]

Rules:
1. Use full-text search: CALL db.index.fulltext.queryNodes('productSearch', '<search_terms>') YIELD node RETURN node LIMIT 10
2. For brand/color filters, add WHERE clauses after the fulltext call
3. For price ranges, use WHERE node.price <= <amount> or node.price >= <amount>
4. Always use the fulltext index as the starting point for text search
5. Return the product node as 'node' (not 'p')

Examples:
- "red nike shoes under $100" -> CALL db.index.fulltext.queryNodes('productSearch', 'nike shoes') YIELD node WHERE node.color = 'Red' AND node.price <= 100 RETURN node LIMIT 10
- "apple laptop" -> CALL db.index.fulltext.queryNodes('productSearch', 'apple laptop') YIELD node RETURN node LIMIT 10
- "samsung phone blue" -> CALL db.index.fulltext.queryNodes('productSearch', 'samsung phone') YIELD node WHERE node.color = 'Blue' RETURN node LIMIT 10

Return ONLY the Cypher query, no explanations."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Convert this to Cypher: {user_query}"}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            cypher = response.choices[0].message.content.strip()
            
            # Clean up markdown code blocks if present
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
            # Fallback
            return f"CALL db.index.fulltext.queryNodes('productSearch', '{user_query}') YIELD node RETURN node LIMIT 10"
    
    def generate_search_query_for_semantic(self, user_query: str) -> str:
        """Generate optimized search query for semantic engine."""
        if not self.client:
            return user_query
        
        system_prompt = """Extract the core search terms from a user query for semantic search.
Remove filler words, keep only important keywords.

Examples:
- "I want red nike running shoes under $100" -> "red nike running shoes"
- "Looking for a comfortable leather jacket" -> "comfortable leather jacket"
- "Apple MacBook Pro 16 inch" -> "Apple MacBook Pro"

Return only the cleaned search terms, no explanations."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate semantic query: {e}")
            return user_query
