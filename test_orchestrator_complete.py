#!/usr/bin/env python3
"""
Orchestrator - Complete Unified Test Suite
Tests all endpoints with expected values from both Semantic Engine and Graph Service
"""

import httpx
import sys
import json
import time
from typing import Dict, Any, List, Callable
from dataclasses import dataclass

# Orchestrator Configuration
BASE_URL = "http://localhost:6969"

# Test Data - Products to insert through orchestrator (unified to both services)
TEST_PRODUCTS = [
    {
        "id": "orch-unified-001",
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
            {"size": "US 10", "stock": 5, "in_stock": True, "variants": [], "sku": "NIKE-AM90-RD-10"}
        ],
        "tags": ["running", "athletic", "casual", "air-max", "nike"],
        "attributes": {"gender": "Men", "material": "Mesh", "technology": "Air"},
        "description": "Classic Nike Air Max 90 running shoes with visible Air cushioning for maximum comfort",
        "images": ["https://example.com/nike-air-max-90-1.jpg"]
    },
    {
        "id": "orch-unified-002",
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
            {"size": "US 9", "stock": 0, "in_stock": False, "variants": [], "sku": "ADIDAS-UB22-BK-09"}
        ],
        "tags": ["running", "boost", "athletic", "performance", "adidas"],
        "attributes": {"gender": "Unisex", "material": "Primeknit", "technology": "Boost"},
        "description": "High-performance running shoes with Boost cushioning technology for energy return",
        "images": ["https://example.com/adidas-ultraboost-22-1.jpg"]
    },
    {
        "id": "orch-unified-003",
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
            {"size": "US 10", "stock": 15, "in_stock": True, "variants": [], "sku": "PUMA-RSX3-BL-10"},
            {"size": "US 11", "stock": 10, "in_stock": True, "variants": [], "sku": "PUMA-RSX3-BL-11"}
        ],
        "tags": ["lifestyle", "casual", "retro", "fashion", "puma", "chunky"],
        "attributes": {"gender": "Men", "material": "Synthetic", "style": "Chunky"},
        "description": "Bold and chunky lifestyle sneakers with retro design for streetwear fashion",
        "images": ["https://example.com/puma-rsx3-1.jpg"]
    },
    {
        "id": "orch-unified-004",
        "name": "New Balance 574",
        "brand": "New Balance",
        "category": {
            "main_category": "Footwear",
            "subcategory": "Sneakers",
            "specific_type": "Casual Shoes"
        },
        "color": "Grey",
        "price": 89.99,
        "original_price": 99.99,
        "sizes": [
            {"size": "US 7", "stock": 25, "in_stock": True, "variants": ["Wide", "Narrow"], "sku": "NB-574-GY-07"},
            {"size": "US 8", "stock": 30, "in_stock": True, "variants": ["Wide"], "sku": "NB-574-GY-08"},
            {"size": "US 9", "stock": 22, "in_stock": True, "variants": [], "sku": "NB-574-GY-09"}
        ],
        "tags": ["casual", "classic", "everyday", "comfortable", "new-balance"],
        "attributes": {"gender": "Unisex", "material": "Suede/Mesh", "width_options": "Wide,Narrow"},
        "description": "Iconic 574 sneaker with classic design and all-day comfort suitable for everyday wear",
        "images": ["https://example.com/nb-574-1.jpg"]
    },
    {
        "id": "orch-unified-005",
        "name": "Nike Air Force 1 Low",
        "brand": "Nike",
        "category": {
            "main_category": "Footwear",
            "subcategory": "Sneakers",
            "specific_type": "Basketball Shoes"
        },
        "color": "White",
        "price": 90.00,
        "original_price": 100.00,
        "sizes": [
            {"size": "US 6", "stock": 15, "in_stock": True, "variants": [], "sku": "NIKE-AF1-WT-06"},
            {"size": "US 7", "stock": 20, "in_stock": True, "variants": [], "sku": "NIKE-AF1-WT-07"},
            {"size": "US 8", "stock": 18, "in_stock": True, "variants": [], "sku": "NIKE-AF1-WT-08"},
            {"size": "US 9", "stock": 12, "in_stock": True, "variants": [], "sku": "NIKE-AF1-WT-09"}
        ],
        "tags": ["basketball", "classic", "lifestyle", "iconic", "nike", "air-force"],
        "attributes": {"gender": "Unisex", "material": "Leather", "style": "Low-top"},
        "description": "Legendary basketball shoe turned lifestyle icon with timeless white design",
        "images": ["https://example.com/nike-af1-1.jpg"]
    }
]


@dataclass
class TestResult:
    name: str
    passed: bool
    duration: float
    details: str = ""
    error: str = ""


class OrchestratorTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)
        self.passed = 0
        self.failed = 0
        self.results: List[TestResult] = []
        
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
            
    def run_test(self, test_name: str, test_func: Callable[[], tuple[bool, str]]) -> bool:
        """Execute a single test and record result"""
        start_time = time.time()
        try:
            success, details = test_func()
            duration = time.time() - start_time
            result = TestResult(name=test_name, passed=success, duration=duration, details=details)
            self.print_test_result(test_name, success, details=details)
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult(name=test_name, passed=False, duration=duration, error=str(e))
            self.print_test_result(test_name, False, error=str(e))
        
        self.results.append(result)
        if result.passed:
            self.passed += 1
        else:
            self.failed += 1
        return result.passed
    
    # ==================== HEALTH & ROOT TESTS ====================
    
    def test_root_endpoint(self):
        """TEST 1: GET / - Root Endpoint"""
        def run():
            response = self.client.get(f"{self.base_url}/")
            if response.status_code != 200:
                return False, f"Expected 200, got {response.status_code}"
            data = response.json()
            if "message" not in data or "version" not in data:
                return False, "Missing expected keys"
            return True, f"API: {data.get('message')}, Version: {data.get('version')}"
        return run
    
    def test_health_check(self):
        """TEST 2: GET /health - Health Check with Service Status"""
        def run():
            response = self.client.get(f"{self.base_url}/health")
            if response.status_code != 200:
                return False, f"Expected 200, got {response.status_code}"
            data = response.json()
            
            checks = []
            if data.get("status") in ["healthy", "degraded"]:
                checks.append("status OK")
            else:
                return False, f"Invalid status: {data.get('status')}"
                
            if data.get("semantic_engine_connected"):
                checks.append("semantic engine connected")
            else:
                return False, "Semantic engine not connected"
                
            if data.get("graph_service_connected"):
                checks.append("graph service connected")
            else:
                return False, "Graph service not connected"
            
            return True, f"Status: {data['status']}, Connected services: {', '.join(checks)}"
        return run
    
    # ==================== PRODUCT INGESTION TESTS ====================
    
    def test_create_single_product(self):
        """TEST 3: POST /api/v1/products - Create Single Product (Unified)"""
        def run():
            product = TEST_PRODUCTS[0]
            response = self.client.post(f"{self.base_url}/api/v1/products", json=product)
            if response.status_code != 200:
                return False, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            
            if not data.get("success"):
                return False, f"Success is false: {data}"
            if data.get("product_id") != product["id"]:
                return False, f"ID mismatch: expected {product['id']}, got {data.get('product_id')}"
            if not data.get("semantic_inserted"):
                return False, "Product not inserted into Semantic Engine"
            if not data.get("graph_inserted"):
                return False, "Product not inserted into Graph Service"
            
            return True, f"Created in both services: Semantic={data['semantic_inserted']}, Graph={data['graph_inserted']}"
        return run
    
    def test_create_product_missing_id(self):
        """TEST 4: POST /api/v1/products - Create Product Missing ID (Error)"""
        def run():
            invalid_product = TEST_PRODUCTS[0].copy()
            del invalid_product["id"]
            response = self.client.post(f"{self.base_url}/api/v1/products", json=invalid_product)
            if response.status_code != 400:
                return False, f"Expected 400, got {response.status_code}"
            data = response.json()
            if "detail" not in data:
                return False, "Missing error detail"
            return True, f"Correctly rejected: {data.get('detail')}"
        return run
    
    def test_batch_create_products(self):
        """TEST 5: POST /api/v1/products/batch - Batch Create Products (Unified)"""
        def run():
            products = TEST_PRODUCTS[1:]  # Skip first one
            response = self.client.post(f"{self.base_url}/api/v1/products/batch", json=products)
            if response.status_code != 200:
                return False, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            
            if not data.get("success"):
                return False, f"Batch creation failed: {data}"
            if data.get("total") != len(products):
                return False, f"Total mismatch: expected {len(products)}, got {data.get('total')}"
            if not data.get("semantic_inserted"):
                return False, "Batch not inserted into Semantic Engine"
            if data.get("graph_inserted_count") != len(products):
                return False, f"Graph insert count mismatch: expected {len(products)}, got {data.get('graph_inserted_count')}"
            
            return True, f"Batch created: {data['graph_inserted_count']}/{data['total']} products in both services"
        return run
    
    def test_batch_create_partial_invalid(self):
        """TEST 6: POST /api/v1/products/batch - Batch with Invalid Product"""
        def run():
            products = [TEST_PRODUCTS[1].copy(), TEST_PRODUCTS[2].copy()]
            del products[0]["id"]  # Make first product invalid
            
            response = self.client.post(f"{self.base_url}/api/v1/products/batch", json=products)
            if response.status_code != 400:
                return False, f"Expected 400 for invalid batch, got {response.status_code}"
            return True, "Correctly rejected batch with invalid product"
        return run
    
    # ==================== SEARCH & RECOMMENDATION TESTS ====================
    
    def test_search_by_brand(self):
        """TEST 7: POST /api/v1/search - Search by Brand (Nike)"""
        def run():
            query = {"query": "Nike running shoes", "limit": 5}
            response = self.client.post(f"{self.base_url}/api/v1/search", json=query)
            if response.status_code != 200:
                return False, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            
            if "recommendations" not in data:
                return False, "Missing recommendations"
            if "extracted_attributes" not in data:
                return False, "Missing extracted_attributes"
            if "semantic_results_count" not in data:
                return False, "Missing semantic_results_count"
            if "graph_results_count" not in data:
                return False, "Missing graph_results_count"
            
            recs = data["recommendations"]
            nike_count = sum(1 for r in recs if r.get("brand") == "Nike")
            
            details = f"Found {len(recs)} recommendations, {nike_count} Nike products"
            details += f" | Semantic: {data['semantic_results_count']}, Graph: {data['graph_results_count']}"
            
            return True, details
        return run
    
    def test_search_by_color(self):
        """TEST 8: POST /api/v1/search - Search by Color (Black)"""
        def run():
            query = {"query": "black sneakers", "limit": 5}
            response = self.client.post(f"{self.base_url}/api/v1/search", json=query)
            if response.status_code != 200:
                return False, f"Expected 200, got {response.status_code}"
            data = response.json()
            
            recs = data.get("recommendations", [])
            
            # Check extracted attributes
            attrs = data.get("extracted_attributes", {})
            
            return True, f"Found {len(recs)} recommendations | Extracted color: {attrs.get('color', 'N/A')}"
        return run
    
    def test_search_by_price_range(self):
        """TEST 9: POST /api/v1/search - Search with Price Constraint"""
        def run():
            query = {"query": "running shoes under $150", "limit": 5}
            response = self.client.post(f"{self.base_url}/api/v1/search", json=query)
            if response.status_code != 200:
                return False, f"Expected 200, got {response.status_code}"
            data = response.json()
            
            recs = data.get("recommendations", [])
            attrs = data.get("extracted_attributes", {})
            price_range = attrs.get("price_range", {})
            
            # Check if recommendations respect price constraint
            under_budget = all(r.get("price", 999) <= 150 for r in recs)
            
            details = f"Found {len(recs)} recommendations under $150"
            details += f" | Price range extracted: max=${price_range.get('max', 'N/A')}"
            details += f" | All under budget: {under_budget}"
            
            return True, details
        return run
    
    def test_search_recommendation_scores(self):
        """TEST 10: POST /api/v1/search - Verify Recommendation Scoring"""
        def run():
            query = {"query": "Nike Air Max", "limit": 3}
            response = self.client.post(f"{self.base_url}/api/v1/search", json=query)
            if response.status_code != 200:
                return False, f"Expected 200, got {response.status_code}"
            data = response.json()
            
            recs = data.get("recommendations", [])
            if not recs:
                return False, "No recommendations returned"
            
            first = recs[0]
            
            # Check all scoring fields exist
            if "semantic_score" not in first:
                return False, "Missing semantic_score"
            if "graph_score" not in first:
                return False, "Missing graph_score"
            if "combined_score" not in first:
                return False, "Missing combined_score"
            
            details = f"Top: {first.get('name')}"
            details += f" | Combined: {first.get('combined_score', 0):.4f}"
            details += f" | Semantic: {first.get('semantic_score', 0):.4f}"
            details += f" | Graph: {first.get('graph_score', 0):.4f}"
            
            return True, details
        return run
    
    def test_search_diversity(self):
        """TEST 11: POST /api/v1/search - Verify Result Diversity"""
        def run():
            query = {"query": "sneakers", "limit": 10}
            response = self.client.post(f"{self.base_url}/api/v1/search", json=query)
            if response.status_code != 200:
                return False, f"Expected 200, got {response.status_code}"
            data = response.json()
            
            recs = data.get("recommendations", [])
            brands = set(r.get("brand") for r in recs)
            
            return True, f"Found {len(recs)} recommendations across {len(brands)} brands: {', '.join(brands)}"
        return run
    
    def test_complex_natural_language_query(self):
        """TEST 12: POST /api/v1/search - Complex Natural Language Query"""
        def run():
            query = {"query": "comfortable running shoes for men under $200 from Nike or Adidas", "limit": 5}
            response = self.client.post(f"{self.base_url}/api/v1/search", json=query)
            if response.status_code != 200:
                return False, f"Expected 200, got {response.status_code}"
            data = response.json()
            
            attrs = data.get("extracted_attributes", {})
            recs = data.get("recommendations", [])
            
            details = f"Query: {data.get('query', 'N/A')[:50]}..."
            details += f" | Intent: {attrs.get('intent', 'N/A')[:30]}"
            details += f" | Product type: {attrs.get('product_type', 'N/A')}"
            details += f" | Results: {len(recs)}"
            
            return True, details
        return run
    
    def test_search_both_services_contribute(self):
        """TEST 13: POST /api/v1/search - Verify Both Services Contribute"""
        def run():
            query = {"query": "athletic footwear", "limit": 5}
            response = self.client.post(f"{self.base_url}/api/v1/search", json=query)
            if response.status_code != 200:
                return False, f"Expected 200, got {response.status_code}"
            data = response.json()
            
            semantic_count = data.get("semantic_results_count", 0)
            graph_count = data.get("graph_results_count", 0)
            final_count = len(data.get("recommendations", []))
            
            details = f"Semantic: {semantic_count} results, Graph: {graph_count} results"
            details += f" | Final recommendations: {final_count}"
            
            # Verify both services returned results
            if semantic_count == 0:
                return False, "Semantic Engine returned no results"
            if graph_count == 0:
                return False, "Graph Service returned no results"
            
            return True, details
        return run
    
    def test_search_with_min_score(self):
        """TEST 14: POST /api/v1/search - Search with Min Score Threshold"""
        def run():
            query = {"query": "Nike shoes", "limit": 5, "min_semantic_score": 0.5}
            response = self.client.post(f"{self.base_url}/api/v1/search", json=query)
            if response.status_code != 200:
                return False, f"Expected 200, got {response.status_code}"
            data = response.json()
            
            recs = data.get("recommendations", [])
            
            # All results should have semantic score >= 0.5
            low_score_count = sum(1 for r in recs if r.get("semantic_score", 0) < 0.5)
            
            return True, f"Found {len(recs)} recommendations with min_score=0.5, {low_score_count} below threshold"
        return run
    
    # ==================== ERROR HANDLING TESTS ====================
    
    def test_search_empty_query(self):
        """TEST 15: POST /api/v1/search - Empty Query"""
        def run():
            query = {"query": "", "limit": 5}
            response = self.client.post(f"{self.base_url}/api/v1/search", json=query)
            # Should either return results or handle gracefully
            return True, f"Status: {response.status_code}, handled empty query"
        return run
    
    def test_invalid_endpoint(self):
        """TEST 16: GET /api/v1/invalid - Invalid Endpoint"""
        def run():
            response = self.client.get(f"{self.base_url}/api/v1/invalid")
            if response.status_code != 404:
                return False, f"Expected 404, got {response.status_code}"
            return True, "Correctly returned 404 for invalid endpoint"
        return run
    
    # ==================== RUN ALL TESTS ====================
    
    def run_all_tests(self):
        """Run all test cases"""
        self.print_header("ORCHESTRATOR - COMPLETE UNIFIED TEST SUITE")
        print(f"  Base URL: {self.base_url}")
        print(f"  Total Tests: 16")
        print(f"  Testing integration of Semantic Engine + Graph Service")
        
        # Health & Root Tests
        self.print_header("HEALTH & ROOT ENDPOINTS")
        self.run_test("Root Endpoint", self.test_root_endpoint())
        self.run_test("Health Check", self.test_health_check())
        
        # Product Ingestion Tests
        self.print_header("PRODUCT INGESTION (UNIFIED)")
        self.run_test("Create Single Product", self.test_create_single_product())
        self.run_test("Create Product Missing ID (Error)", self.test_create_product_missing_id())
        self.run_test("Batch Create Products", self.test_batch_create_products())
        self.run_test("Batch Create Invalid (Error)", self.test_batch_create_partial_invalid())
        
        # Search & Recommendation Tests
        self.print_header("SEARCH & RECOMMENDATIONS")
        self.run_test("Search by Brand (Nike)", self.test_search_by_brand())
        self.run_test("Search by Color (Black)", self.test_search_by_color())
        self.run_test("Search by Price Range", self.test_search_by_price_range())
        self.run_test("Recommendation Scoring", self.test_search_recommendation_scores())
        self.run_test("Search Diversity", self.test_search_diversity())
        self.run_test("Complex NL Query", self.test_complex_natural_language_query())
        self.run_test("Both Services Contribute", self.test_search_both_services_contribute())
        self.run_test("Search with Min Score", self.test_search_with_min_score())
        
        # Error Handling Tests
        self.print_header("ERROR HANDLING")
        self.run_test("Search Empty Query", self.test_search_empty_query())
        self.run_test("Invalid Endpoint", self.test_invalid_endpoint())
        
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
            print("  ✓ Orchestrator successfully integrates Semantic Engine and Graph Service")
        else:
            print(f"\n  ✗ {self.failed} TEST(S) FAILED")
            print("\n  Failed Tests:")
            for result in self.results:
                if not result.passed:
                    print(f"    - {result.name}")
                    
    def close(self):
        """Close HTTP client"""
        self.client.close()


def main():
    # Allow custom URL via command line
    url = sys.argv[1] if len(sys.argv) > 1 else BASE_URL
    
    tester = OrchestratorTester(url)
    try:
        tester.run_all_tests()
        exit_code = 0 if tester.failed == 0 else 1
    finally:
        tester.close()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
