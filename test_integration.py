#!/usr/bin/env python3
"""
Orchestrator Integration Test - Products + Search
This test first inserts products through orchestrator, then tests search
"""

import httpx
import sys
import time

BASE_URL = "http://localhost:6969"

TEST_PRODUCTS = [
    {
        "id": "integration-test-001",
        "name": "Nike Air Max 90",
        "brand": "Nike",
        "category": {"main_category": "Footwear", "subcategory": "Sneakers", "specific_type": "Running Shoes"},
        "color": "Red",
        "price": 129.99,
        "original_price": 159.99,
        "sizes": [{"size": "US 8", "stock": 10, "in_stock": True, "variants": ["Wide"], "sku": "NIKE-AM90-RD-08"}],
        "tags": ["running", "athletic", "nike", "air-max"],
        "attributes": {"gender": "Men", "material": "Mesh"},
        "description": "Classic Nike Air Max 90 running shoes with visible Air cushioning",
        "images": ["https://example.com/nike1.jpg"]
    },
    {
        "id": "integration-test-002",
        "name": "Adidas Ultraboost 22",
        "brand": "Adidas",
        "category": {"main_category": "Footwear", "subcategory": "Sneakers", "specific_type": "Running Shoes"},
        "color": "Black",
        "price": 180.00,
        "original_price": 200.00,
        "sizes": [{"size": "US 8", "stock": 12, "in_stock": True, "variants": [], "sku": "ADIDAS-UB22-BK-08"}],
        "tags": ["running", "boost", "adidas", "performance"],
        "attributes": {"gender": "Unisex", "material": "Primeknit"},
        "description": "High-performance running shoes with Boost cushioning",
        "images": ["https://example.com/adidas1.jpg"]
    },
    {
        "id": "integration-test-003",
        "name": "Puma RS-X3",
        "brand": "Puma",
        "category": {"main_category": "Footwear", "subcategory": "Sneakers", "specific_type": "Lifestyle Shoes"},
        "color": "Blue",
        "price": 110.00,
        "original_price": 110.00,
        "sizes": [{"size": "US 9", "stock": 20, "in_stock": True, "variants": [], "sku": "PUMA-RSX3-BL-09"}],
        "tags": ["lifestyle", "casual", "puma", "retro"],
        "attributes": {"gender": "Men", "material": "Synthetic"},
        "description": "Bold lifestyle sneakers with retro design",
        "images": ["https://example.com/puma1.jpg"]
    }
]

def test_health():
    """Check orchestrator health"""
    response = httpx.get(f"{BASE_URL}/health")
    data = response.json()
    print(f"✓ Health: {data['status']}")
    print(f"  - Semantic Engine: {'✓' if data['semantic_engine_connected'] else '✗'}")
    print(f"  - Graph Service: {'✓' if data['graph_service_connected'] else '✗'}")
    return data['semantic_engine_connected'] and data['graph_service_connected']

def test_insert_products():
    """Insert products through orchestrator"""
    print("\n=== Inserting Products ===")
    
    # Insert single product
    response = httpx.post(f"{BASE_URL}/api/v1/products", json=TEST_PRODUCTS[0])
    if response.status_code != 200:
        print(f"✗ Failed to insert product 1: {response.text}")
        return False
    data = response.json()
    print(f"✓ Inserted product 1: {data['product_id']}")
    print(f"  - Semantic: {data['semantic_inserted']}, Graph: {data['graph_inserted']}")
    
    # Batch insert remaining products
    response = httpx.post(f"{BASE_URL}/api/v1/products/batch", json=TEST_PRODUCTS[1:])
    if response.status_code != 200:
        print(f"✗ Failed batch insert: {response.text}")
        return False
    data = response.json()
    print(f"✓ Batch inserted {data['graph_inserted_count']}/{data['total']} products")
    
    # Wait for indexing
    print("  Waiting for indexing...")
    time.sleep(2)
    return True

def test_search():
    """Test search functionality"""
    print("\n=== Testing Search ===")
    
    tests = [
        ("Search by brand (Nike)", {"query": "Nike shoes", "limit": 5}),
        ("Search by color (Black)", {"query": "black sneakers", "limit": 5}),
        ("Search by price range", {"query": "running shoes under $150", "limit": 5}),
        ("Complex query", {"query": "comfortable running shoes for men", "limit": 5}),
    ]
    
    all_passed = True
    for test_name, query_payload in tests:
        response = httpx.post(f"{BASE_URL}/api/v1/search", json=query_payload)
        if response.status_code != 200:
            print(f"✗ {test_name}: HTTP {response.status_code}")
            all_passed = False
            continue
        
        data = response.json()
        recs = data.get('recommendations', [])
        semantic_count = data.get('semantic_results_count', 0)
        graph_count = data.get('graph_results_count', 0)
        
        if len(recs) == 0:
            print(f"✗ {test_name}: No recommendations")
            print(f"    Semantic: {semantic_count}, Graph: {graph_count}")
            all_passed = False
        else:
            print(f"✓ {test_name}: {len(recs)} recommendations")
            print(f"    Query: '{data.get('query', 'N/A')[:40]}...'")
            print(f"    Semantic: {semantic_count}, Graph: {graph_count}")
            if recs:
                print(f"    Top: {recs[0].get('name', 'N/A')} (score: {recs[0].get('combined_score', 0):.3f})")
    
    return all_passed

def main():
    print("="*80)
    print("ORCHESTRATOR INTEGRATION TEST")
    print("="*80)
    
    # Check health
    if not test_health():
        print("\n✗ Services not healthy. Exiting.")
        sys.exit(1)
    
    # Insert products
    if not test_insert_products():
        print("\n✗ Failed to insert products. Exiting.")
        sys.exit(1)
    
    # Test search
    if test_search():
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED!")
        print("="*80)
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("✗ SOME TESTS FAILED")
        print("="*80)
        sys.exit(1)

if __name__ == "__main__":
    main()
