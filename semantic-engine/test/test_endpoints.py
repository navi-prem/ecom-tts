#!/usr/bin/env python3
"""Test script for all vector search API endpoints"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

def print_response(response, title):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    return response.status_code < 400

def test_health():
    """Test health endpoint"""
    print("\n>>> Testing Health Endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    return print_response(response, "HEALTH CHECK")

def test_add_single_product():
    """Test adding a single product"""
    print("\n>>> Testing Add Single Product...")
    
    product = {
        "id": "prod_001",
        "name": "Running Shoes",
        "brand": "Nike",
        "category": {
            "main_category": "Footwear",
            "subcategory": "Shoes",
            "specific_type": "Running"
        },
        "color": "Black",
        "price": 5999.99,
        "original_price": 7999.99,
        "sizes": [
            {"size": "9", "variants": ["regular", "wide"], "sku": "NIKE-RUN-9-BLK"},
            {"size": "10", "variants": ["regular"], "sku": "NIKE-RUN-10-BLK"}
        ],
        "tags": ["sports", "running", "shoes"],
        "attributes": {
            "material": "mesh",
            "gender": "men",
            "sole": "rubber"
        },
        "description": "Lightweight running shoes with breathable mesh and durable sole.",
        "images": ["https://example.com/images/shoe1.jpg"]
    }
    
    response = requests.post(f"{API_URL}/products", json=product)
    return print_response(response, "ADD SINGLE PRODUCT")

def test_add_batch_products():
    """Test batch product insertion"""
    print("\n>>> Testing Batch Product Insert...")
    
    products = [
        {
            "id": "prod_002",
            "name": "Wireless Bluetooth Headphones",
            "brand": "Sony",
            "category": {
                "main_category": "Electronics",
                "subcategory": "Audio",
                "specific_type": "Headphones"
            },
            "color": "Black",
            "price": 8999.99,
            "original_price": 11999.99,
            "sizes": [],
            "tags": ["electronics", "audio", "wireless", "bluetooth"],
            "attributes": {
                "material": "plastic",
                "gender": "unisex",
                "battery_life": "30 hours"
            },
            "description": "Premium wireless headphones with active noise cancellation and 30-hour battery life.",
            "images": ["https://example.com/images/headphones1.jpg"]
        },
        {
            "id": "prod_003",
            "name": "Yoga Mat",
            "brand": "Lululemon",
            "category": {
                "main_category": "Fitness",
                "subcategory": "Yoga",
                "specific_type": "Mats"
            },
            "color": "Purple",
            "price": 2499.99,
            "original_price": 2999.99,
            "sizes": [{"size": "Standard", "variants": ["regular"], "sku": "LULU-YOGA-PUR"}],
            "tags": ["fitness", "yoga", "exercise", "mat"],
            "attributes": {
                "material": "rubber",
                "gender": "unisex",
                "thickness": "5mm"
            },
            "description": "Non-slip yoga mat with extra cushioning for joint support during practice.",
            "images": ["https://example.com/images/yogamat1.jpg"]
        },
        {
            "id": "prod_004",
            "name": "Basketball Shoes",
            "brand": "Nike",
            "category": {
                "main_category": "Footwear",
                "subcategory": "Shoes",
                "specific_type": "Basketball"
            },
            "color": "Red",
            "price": 7499.99,
            "original_price": 8999.99,
            "sizes": [
                {"size": "10", "variants": ["regular"], "sku": "NIKE-BB-10-RED"}
            ],
            "tags": ["sports", "basketball", "shoes"],
            "attributes": {
                "material": "leather",
                "gender": "men",
                "sole": "rubber"
            },
            "description": "High-performance basketball shoes with ankle support and superior traction.",
            "images": ["https://example.com/images/bball_shoe1.jpg"]
        }
    ]
    
    response = requests.post(f"{API_URL}/products/batch", json={"products": products})
    return print_response(response, "BATCH INSERT")

def test_search():
    """Test search functionality"""
    print("\n>>> Testing Search...")
    
    # Basic search
    search_query = {
        "query": "running shoes for men",
        "limit": 5
    }
    
    response = requests.post(f"{API_URL}/search", json=search_query)
    success = print_response(response, "SEARCH - Running Shoes")
    
    # Search with filters
    print("\n>>> Testing Search with Filters...")
    filtered_search = {
        "query": "shoes",
        "limit": 10,
        "filters": {
            "brand": "Nike"
        }
    }
    
    response = requests.post(f"{API_URL}/search", json=filtered_search)
    return print_response(response, "SEARCH - Filtered by Brand (Nike)") and success

def test_get_product():
    """Test getting a product by ID"""
    print("\n>>> Testing Get Product by ID...")
    response = requests.get(f"{API_URL}/products/prod_001")
    return print_response(response, "GET PRODUCT")

def test_delete_product():
    """Test deleting a product"""
    print("\n>>> Testing Delete Product...")
    # Delete one of the batch products
    response = requests.delete(f"{API_URL}/products/prod_003")
    success = print_response(response, "DELETE PRODUCT")
    
    # Verify deletion by trying to get it
    print("\n>>> Verifying Deletion...")
    response = requests.get(f"{API_URL}/products/prod_003")
    return print_response(response, "VERIFY DELETION (should be 404)") and success

def run_all_tests():
    """Run all endpoint tests"""
    print("\n" + "="*60)
    print("VECTOR SEARCH API - ENDPOINT TESTS")
    print("="*60)
    
    results = []
    
    # Test 1: Health Check
    results.append(("Health Check", test_health()))
    
    # Test 2: Add Single Product
    results.append(("Add Single Product", test_add_single_product()))
    
    # Test 3: Batch Insert
    results.append(("Batch Insert", test_add_batch_products()))
    
    # Test 4: Search
    results.append(("Search", test_search()))
    
    # Test 5: Get Product
    results.append(("Get Product", test_get_product()))
    
    # Test 6: Delete Product
    results.append(("Delete Product", test_delete_product()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(run_all_tests())
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ ERROR: Cannot connect to server at {BASE_URL}")
        print(f"Make sure the server is running: uvicorn main:app --reload")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
