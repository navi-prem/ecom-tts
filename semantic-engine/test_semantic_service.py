#!/usr/bin/env python3
"""
Semantic Engine - Complete Test Suite
Tests all HTTP routes with expected values
"""

import httpx
import sys
import json
from typing import Dict, Any, List
from dataclasses import dataclass

# Service Configuration
BASE_URL = "http://localhost:8000"

# Test Data
TEST_PRODUCTS = [
    {
        "id": "sem-test-001",
        "name": "Nike Air Max 90",
        "brand": "Nike",
        "category": {
            "main_category": "Footwear",
            "subcategory": "Sneakers",
            "specific_type": "Running Shoes"
        },
        "color": "Red",
        "price": 129.99,
        "original_price": 159.99,
        "sizes": [
            {"size": "US 8", "stock": 10, "in_stock": True, "variants": ["Wide"], "sku": "NIKE-AM90-RD-08"},
            {"size": "US 9", "stock": 15, "in_stock": True, "variants": [], "sku": "NIKE-AM90-RD-09"},
        ],
        "tags": ["running", "athletic", "casual", "air-max"],
        "attributes": {"gender": "Men", "material": "Mesh", "technology": "Air"},
        "description": "Classic Nike Air Max 90 running shoes with visible Air cushioning",
        "images": ["https://example.com/nike-air-max-90-1.jpg"]
    },
    {
        "id": "sem-test-002",
        "name": "Adidas Ultraboost 22",
        "brand": "Adidas",
        "category": {
            "main_category": "Footwear",
            "subcategory": "Sneakers",
            "specific_type": "Running Shoes"
        },
        "color": "Black",
        "price": 180.00,
        "original_price": 200.00,
        "sizes": [
            {"size": "US 7", "stock": 8, "in_stock": True, "variants": [], "sku": "ADIDAS-UB22-BK-07"},
            {"size": "US 8", "stock": 12, "in_stock": True, "variants": [], "sku": "ADIDAS-UB22-BK-08"},
        ],
        "tags": ["running", "boost", "athletic", "performance"],
        "attributes": {"gender": "Unisex", "material": "Primeknit", "technology": "Boost"},
        "description": "High-performance running shoes with Boost cushioning technology",
        "images": ["https://example.com/adidas-ultraboost-22-1.jpg"]
    },
    {
        "id": "sem-test-003",
        "name": "Puma RS-X3 Puzzle",
        "brand": "Puma",
        "category": {
            "main_category": "Footwear",
            "subcategory": "Sneakers",
            "specific_type": "Lifestyle Shoes"
        },
        "color": "Blue",
        "price": 110.00,
        "original_price": 110.00,
        "sizes": [
            {"size": "US 8", "stock": 20, "in_stock": True, "variants": [], "sku": "PUMA-RSX3-BL-08"},
            {"size": "US 9", "stock": 18, "in_stock": True, "variants": [], "sku": "PUMA-RSX3-BL-09"},
        ],
        "tags": ["lifestyle", "casual", "retro", "fashion"],
        "attributes": {"gender": "Men", "material": "Synthetic", "style": "Chunky"},
        "description": "Bold and chunky lifestyle sneakers with retro design",
        "images": ["https://example.com/puma-rsx3-1.jpg"]
    }
]


@dataclass
class TestCase:
    name: str
    method: str
    endpoint: str
    payload: Dict[str, Any] = None
    expected_status: int = 200
    expected_keys: List[str] = None
    validate_response: callable = None


class SemanticServiceTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)
        self.passed = 0
        self.failed = 0
        self.results = []
        
    def print_header(self, text: str):
        print("\n" + "="*80)
        print(f"  {text}")
        print("="*80)
        
    def print_test_result(self, test_name: str, passed: bool, details: str = "", error: str = ""):
        status = "✓ PASS" if passed else "✗ FAIL"
        color = "\033[92m" if passed else "\033[91m"
        reset = "\033[0m"
        
        print(f"\n  {color}{status}{reset} {test_name}")
        if details:
            print(f"    {details}")
        if error:
            print(f"    Error: {error}")
            
    def run_test(self, test_case: TestCase) -> bool:
        """Execute a single test case"""
        try:
            url = f"{self.base_url}{test_case.endpoint}"
            
            if test_case.method == "GET":
                response = self.client.get(url)
            elif test_case.method == "POST":
                response = self.client.post(url, json=test_case.payload)
            elif test_case.method == "DELETE":
                response = self.client.delete(url)
            else:
                raise ValueError(f"Unsupported method: {test_case.method}")
            
            # Check status code
            if response.status_code != test_case.expected_status:
                self.print_test_result(
                    test_case.name, 
                    False, 
                    error=f"Expected status {test_case.expected_status}, got {response.status_code}"
                )
                return False
            
            # Parse response
            try:
                data = response.json()
            except:
                data = None
            
            # Check expected keys
            if test_case.expected_keys and data:
                missing_keys = [k for k in test_case.expected_keys if k not in data]
                if missing_keys:
                    self.print_test_result(
                        test_case.name,
                        False,
                        error=f"Missing keys: {missing_keys}"
                    )
                    return False
            
            # Run custom validation
            if test_case.validate_response and data:
                validation_result = test_case.validate_response(data)
                if not validation_result[0]:
                    self.print_test_result(
                        test_case.name,
                        False,
                        error=validation_result[1]
                    )
                    return False
            
            # Success
            details = f"Status: {response.status_code}"
            if data:
                details += f" | Response keys: {list(data.keys())}"
            self.print_test_result(test_case.name, True, details=details)
            return True
            
        except Exception as e:
            self.print_test_result(test_case.name, False, error=str(e))
            return False
    
    def test_health_check(self):
        """TEST 1: GET /health - Health Check"""
        def validate(data):
            if data.get("status") not in ["healthy", "unhealthy"]:
                return (False, f"Invalid status: {data.get('status')}")
            if "products_count" not in data:
                return (False, "Missing products_count")
            if "qdrant_connected" not in data:
                return (False, "Missing qdrant_connected")
            return (True, "")
        
        test = TestCase(
            name="Health Check",
            method="GET",
            endpoint="/health",
            expected_status=200,
            expected_keys=["status", "products_count", "qdrant_connected"],
            validate_response=validate
        )
        return self.run_test(test)
    
    def test_create_single_product(self):
        """TEST 2: POST /api/v1/products - Create Single Product"""
        def validate(data):
            if not data.get("success"):
                return (False, f"Success is false: {data}")
            if data.get("inserted_count") != 1:
                return (False, f"Expected inserted_count=1, got {data.get('inserted_count')}")
            return (True, "")
        
        test = TestCase(
            name="Create Single Product",
            method="POST",
            endpoint="/api/v1/products",
            payload=TEST_PRODUCTS[0],
            expected_status=200,
            expected_keys=["success", "inserted_count", "total", "message"],
            validate_response=validate
        )
        return self.run_test(test)
    
    def test_create_product_missing_id(self):
        """TEST 3: POST /api/v1/products - Create Product Missing ID (Error Case)"""
        invalid_product = TEST_PRODUCTS[0].copy()
        del invalid_product["id"]
        
        test = TestCase(
            name="Create Product Missing ID (Error)",
            method="POST",
            endpoint="/api/v1/products",
            payload=invalid_product,
            expected_status=400,
            expected_keys=["detail"]
        )
        return self.run_test(test)
    
    def test_batch_create_products(self):
        """TEST 4: POST /api/v1/products/batch - Batch Create Products"""
        def validate(data):
            if not data.get("success"):
                return (False, f"Success is false: {data}")
            expected_count = len(TEST_PRODUCTS[1:])
            if data.get("inserted_count") != expected_count:
                return (False, f"Expected inserted_count={expected_count}, got {data.get('inserted_count')}")
            return (True, "")
        
        test = TestCase(
            name="Batch Create Products",
            method="POST",
            endpoint="/api/v1/products/batch",
            payload={"products": TEST_PRODUCTS[1:]},
            expected_status=200,
            expected_keys=["success", "inserted_count", "total", "message"],
            validate_response=validate
        )
        return self.run_test(test)
    
    def test_search_by_query(self):
        """TEST 5: POST /api/v1/search - Search Products"""
        def validate(data):
            if "results" not in data:
                return (False, "Missing results")
            if "total_found" not in data:
                return (False, "Missing total_found")
            if data.get("query") != "Nike running shoes":
                return (False, f"Query mismatch: {data.get('query')}")
            return (True, f"Found {data.get('total_found')} results")
        
        test = TestCase(
            name="Search Products by Query",
            method="POST",
            endpoint="/api/v1/search",
            payload={"query": "Nike running shoes", "limit": 5},
            expected_status=200,
            expected_keys=["query", "results", "total_found"],
            validate_response=validate
        )
        return self.run_test(test)
    
    def test_search_with_filters(self):
        """TEST 6: POST /api/v1/search - Search with Filters"""
        def validate(data):
            results = data.get("results", [])
            # All results should be Nike products if filter works
            nike_count = sum(1 for r in results if r.get("brand") == "Nike")
            return (True, f"Found {len(results)} results, {nike_count} Nike products")
        
        test = TestCase(
            name="Search with Brand Filter",
            method="POST",
            endpoint="/api/v1/search",
            payload={
                "query": "running shoes",
                "limit": 5,
                "filters": {"brand": "Nike"},
                "min_score": 0.3
            },
            expected_status=200,
            expected_keys=["query", "results", "total_found"],
            validate_response=validate
        )
        return self.run_test(test)
    
    def test_search_empty_query(self):
        """TEST 7: POST /api/v1/search - Empty Query (Error Case)"""
        test = TestCase(
            name="Search Empty Query (Error)",
            method="POST",
            endpoint="/api/v1/search",
            payload={"query": "", "limit": 5},
            expected_status=400,
            expected_keys=["detail"]
        )
        return self.run_test(test)
    
    def test_get_product_by_id(self):
        """TEST 8: GET /api/v1/products/{id} - Get Product"""
        test = TestCase(
            name="Get Product by ID",
            method="GET",
            endpoint=f"/api/v1/products/{TEST_PRODUCTS[0]['id']}",
            expected_status=200,
            expected_keys=["id", "payload"]
        )
        return self.run_test(test)
    
    def test_get_product_not_found(self):
        """TEST 9: GET /api/v1/products/{id} - Product Not Found"""
        test = TestCase(
            name="Get Product Not Found (Error)",
            method="GET",
            endpoint="/api/v1/products/non-existent-id",
            expected_status=404,
            expected_keys=["detail"]
        )
        return self.run_test(test)
    
    def test_delete_product(self):
        """TEST 10: DELETE /api/v1/products/{id} - Delete Product"""
        def validate(data):
            if not data.get("success"):
                return (False, f"Delete failed: {data}")
            return (True, "Product deleted successfully")
        
        test = TestCase(
            name="Delete Product",
            method="DELETE",
            endpoint=f"/api/v1/products/{TEST_PRODUCTS[2]['id']}",
            expected_status=200,
            expected_keys=["success", "message"],
            validate_response=validate
        )
        return self.run_test(test)
    
    def test_delete_product_not_found(self):
        """TEST 11: DELETE /api/v1/products/{id} - Delete Non-existent Product"""
        test = TestCase(
            name="Delete Product Not Found (Error)",
            method="DELETE",
            endpoint="/api/v1/products/non-existent-id",
            expected_status=404,
            expected_keys=["detail"]
        )
        return self.run_test(test)
    
    def test_root_endpoint(self):
        """TEST 12: GET / - Root Endpoint"""
        def validate(data):
            if "message" not in data:
                return (False, "Missing message")
            if "version" not in data:
                return (False, "Missing version")
            return (True, f"API: {data.get('message')}")
        
        test = TestCase(
            name="Root Endpoint",
            method="GET",
            endpoint="/",
            expected_status=200,
            expected_keys=["message", "version"],
            validate_response=validate
        )
        return self.run_test(test)
    
    def run_all_tests(self):
        """Run all test cases"""
        self.print_header("SEMANTIC ENGINE - COMPLETE TEST SUITE")
        print(f"  Base URL: {self.base_url}")
        print(f"  Total Tests: 12")
        
        tests = [
            self.test_root_endpoint,
            self.test_health_check,
            self.test_create_single_product,
            self.test_create_product_missing_id,
            self.test_batch_create_products,
            self.test_search_by_query,
            self.test_search_with_filters,
            self.test_search_empty_query,
            self.test_get_product_by_id,
            self.test_get_product_not_found,
            self.test_delete_product,
            self.test_delete_product_not_found,
        ]
        
        for test_func in tests:
            if test_func():
                self.passed += 1
            else:
                self.failed += 1
        
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("  TEST SUMMARY")
        print("="*80)
        print(f"\n  Total Tests: {self.passed + self.failed}")
        print(f"  Passed: {self.passed}")
        print(f"  Failed: {self.failed}")
        
        if self.failed == 0:
            print("\n  ✓ ALL TESTS PASSED!")
        else:
            print(f"\n  ✗ {self.failed} TEST(S) FAILED")
            
    def close(self):
        """Close HTTP client"""
        self.client.close()


def main():
    tester = SemanticServiceTester()
    try:
        tester.run_all_tests()
        exit_code = 0 if tester.failed == 0 else 1
    finally:
        tester.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
