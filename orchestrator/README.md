# Product Search Orchestrator

This service orchestrates search across both the Semantic Engine (vector search with Qdrant) and Graph Service (Neo4j graph database), using LLM-powered query understanding to provide intelligent product recommendations.

## Architecture

```
┌─────────────────┐
│   Orchestrator  │  (Port 6969)
│   (Python/FastAPI)
└────────┬────────┘
         │
    ┌────┴────┐
    │   LLM   │  Query Understanding
    │ (OpenAI)│  Attribute Extraction
    └────┬────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌───▼────┐
│Semantic│ │ Graph │
│ Engine │ │Service│
│(Port   │ │(Port  │
│ 8000)  │ │ 50051)│
│Qdrant  │ │Neo4j  │
└────────┘ └───────┘
```

## Features

1. **LLM Query Processing**: Extracts structured attributes (brand, color, price range, etc.) from natural language queries
2. **Dual Search**: Queries both semantic vector search and graph database in parallel
3. **Smart Recommendations**: Combines results using weighted scoring algorithm
4. **Unified API**: Single endpoint for both search and product management

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export OPENAI_API_KEY="your-api-key"
export SEMANTIC_ENGINE_URL="http://localhost:8000"
export GRAPH_SERVICE_TARGET="localhost:50051"
```

3. Run the service:
```bash
python main.py
```

## API Endpoints

### Search Products
```bash
POST /api/v1/search
{
  "query": "red nike running shoes under $100",
  "limit": 10,
  "min_semantic_score": 0.3
}
```

### Health Check
```bash
GET /health
```

### Create Product
```bash
POST /api/v1/products
{
  "id": "prod-123",
  "name": "Nike Air Max",
  "brand": "Nike",
  ...
}
```

## Recommendation Algorithm

The recommendation service combines results using:
- **Semantic Score** (0.5 weight): Vector similarity from Qdrant
- **Graph Score** (0.5 weight): Attribute matching from Neo4j
- **Diversity Boost** (+0.05): Rewards products found in both sources

Combined score = (0.5 × semantic_score) + (0.5 × graph_score) + diversity_boost

Products are ranked by combined score and filtered for brand/category diversity.
