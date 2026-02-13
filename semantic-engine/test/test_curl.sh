#!/bin/bash
# Sample curl commands to test the Product Vector Search API
# Make sure the server is running: uvicorn main:app --reload

echo "=========================================="
echo "Product Vector Search API - Curl Examples"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8000"
API_URL="$BASE_URL/api/v1"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}1. Health Check${NC}"
echo "----------------------------------------"
curl -s "$BASE_URL/health" | jq .
echo ""

echo -e "${BLUE}2. Add Single Product${NC}"
echo "----------------------------------------"
curl -s -X POST "$API_URL/products" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "prod_curl_001",
    "name": "Gaming Laptop",
    "brand": "ASUS",
    "category": {
      "main_category": "Electronics",
      "subcategory": "Computers",
      "specific_type": "Laptops"
    },
    "color": "Black",
    "price": 89999.99,
    "original_price": 99999.99,
    "sizes": [],
    "tags": ["gaming", "laptop", "high-performance", "rtx"],
    "attributes": {
      "material": "aluminum",
      "gender": "unisex",
      "processor": "Intel i9",
      "ram": "32GB"
    },
    "description": "High-performance gaming laptop with RTX 4080 graphics card and 240Hz display.",
    "images": ["https://example.com/images/laptop1.jpg"]
  }' | jq .
echo ""

echo -e "${BLUE}3. Add Multiple Products (Batch)${NC}"
echo "----------------------------------------"
curl -s -X POST "$API_URL/products/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "products": [
      {
        "id": "prod_curl_002",
        "name": "Mechanical Keyboard",
        "brand": "Keychron",
        "category": {
          "main_category": "Electronics",
          "subcategory": "Accessories",
          "specific_type": "Keyboards"
        },
        "color": "White",
        "price": 7999.99,
        "original_price": 9999.99,
        "sizes": [],
        "tags": ["mechanical", "wireless", "rgb"],
        "attributes": {
          "material": "plastic",
          "gender": "unisex",
          "switches": "Cherry MX Brown"
        },
        "description": "Wireless mechanical keyboard with RGB backlight and hot-swappable switches.",
        "images": ["https://example.com/images/keyboard1.jpg"]
      },
      {
        "id": "prod_curl_003",
        "name": "Running Shorts",
        "brand": "Nike",
        "category": {
          "main_category": "Clothing",
          "subcategory": "Bottoms",
          "specific_type": "Shorts"
        },
        "color": "Blue",
        "price": 2499.99,
        "original_price": 2999.99,
        "sizes": [
          {"size": "M", "variants": ["regular"], "sku": "NIKE-SHORT-M-BLU"},
          {"size": "L", "variants": ["regular"], "sku": "NIKE-SHORT-L-BLU"}
        ],
        "tags": ["sports", "running", "shorts", "men"],
        "attributes": {
          "material": "polyester",
          "gender": "men",
          "fit": "regular"
        },
        "description": "Lightweight running shorts with moisture-wicking fabric and zippered pockets.",
        "images": ["https://example.com/images/shorts1.jpg"]
      }
    ]
  }' | jq .
echo ""

echo -e "${BLUE}4. Search Products (Basic)${NC}"
echo "----------------------------------------"
echo "Query: 'gaming laptop'"
curl -s -X POST "$API_URL/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "gaming laptop",
    "limit": 5
  }' | jq .
echo ""

echo -e "${BLUE}5. Search Products (Filtered by Brand)${NC}"
echo "----------------------------------------"
echo "Query: 'sports' | Filter: brand='Nike'"
curl -s -X POST "$API_URL/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "sports",
    "limit": 10,
    "filters": {
      "brand": "Nike"
    }
  }' | jq .
echo ""

echo -e "${BLUE}6. Search Products (Filtered by Category)${NC}"
echo "----------------------------------------"
echo "Query: 'computer accessories' | Filter: category='Electronics'"
curl -s -X POST "$API_URL/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "computer accessories",
    "limit": 10,
    "filters": {
      "category": "Electronics"
    }
  }' | jq .
echo ""

echo -e "${BLUE}7. Get Product by ID${NC}"
echo "----------------------------------------"
curl -s "$API_URL/products/prod_curl_001" | jq .
echo ""

echo -e "${BLUE}8. Delete Product${NC}"
echo "----------------------------------------"
curl -s -X DELETE "$API_URL/products/prod_curl_002" | jq .
echo ""

echo -e "${BLUE}9. Verify Deletion (Should return 404)${NC}"
echo "----------------------------------------"
curl -s -w "\nHTTP Status: %{http_code}\n" "$API_URL/products/prod_curl_002"
echo ""

echo -e "${BLUE}10. Search with Multiple Filters${NC}"
echo "----------------------------------------"
echo "Query: 'running gear' | Filters: brand='Nike', gender='men'"
curl -s -X POST "$API_URL/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "running gear",
    "limit": 10,
    "filters": {
      "brand": "Nike",
      "gender": "men"
    }
  }' | jq .
echo ""

echo "=========================================="
echo "All curl examples completed!"
echo "=========================================="
