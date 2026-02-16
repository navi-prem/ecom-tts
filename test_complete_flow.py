#!/usr/bin/env python3
"""
Complete Integration Test Suite for E-Commerce TTS
Tests all services: Semantic Engine, Graph Service, and Orchestrator
"""

import asyncio
import httpx
import sys
import json
import time
from typing import Dict, List, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init()

# Configuration
ORCHESTRATOR_URL = "http://localhost:6969"
SEMANTIC_URL = "http://localhost:8000"
GRAPH_URL = "localhost:50051"

# Test Products (Generic - can be any category)
TEST_PRODUCTS = [
    {
        "id": "test-flow-001",
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
            {"size": "US 9", "stock": 15, "in_stock": True, "variants": [], "sku": "NIKE-AM90-RD-09"}
        ],
        "tags": ["running", "athletic", "air-max", "comfortable"],
        "attributes": {"gender": "Men", "material": "Mesh", "technology": "Air"},
        "description": "Classic Nike Air Max 90 running shoes with visible Air cushioning technology for maximum comfort during runs",
        "images": ["https://example.com/nike1.jpg"]
    },
    {
        "id": "test-flow-002",
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
            {"size": "US 8", "stock": 12, "in_stock": True, "variants": [], "sku": "ADIDAS-UB22-BK-08"}
        ],
        "tags": ["running", "boost", "performance", "energy-return"],
        "attributes": {"gender": "Unisex", "material": "Primeknit", "technology": "Boost"},
        "description": "High-performance running shoes with Boost cushioning technology for maximum energy return on every stride",
        "images": ["https://example.com/adidas1.jpg"]
    },
    {
        "id": "test-flow-003",
        "name": "Apple MacBook Pro 16",
        "brand": "Apple",
        "category": {
            "main_category": "Electronics",
            "subcategory": "Computers",
            "specific_type": "Laptops"
        },
        "color": "Space Gray",
        "price": 2499.00,
        "original_price": 2699.00,
        "sizes": [],
        "tags": ["laptop", "professional", "m3-max", "creative"],
        "attributes": {"processor": "M3 Max", "memory": "32GB", "storage": "1TB SSD"},
        "description": "Apple MacBook Pro 16-inch with M3 Max chip, 32GB RAM, and stunning Liquid Retina XDR display for professionals",
        "images": ["https://example.com/macbook1.jpg"]
    },
    {
        "id": "test-flow-004",
        "name": "Sony WH-1000XM5",
        "brand": "Sony",
        "category": {
            "main_category": "Electronics",
            "subcategory": "Audio",
            "specific_type": "Headphones"
        },
        "color": "Black",
        "price": 399.99,
        "original_price": 449.99,
        "sizes": [],
        "tags": ["wireless", "noise-cancelling", "premium", "audio"],
        "attributes": {"type": "Over-ear", "connectivity": "Bluetooth 5.2", "battery": "30 hours"},
        "description": "Industry-leading noise cancelling headphones with exceptional sound quality and 30-hour battery life",
        "images": ["https://example.com/sony1.jpg"]
    }
]


@dataclass
class TestResult:
    """Represents a single test result"""
    name: str
    passed: bool
    duration: float
    details: str = ""
    error: str = ""
    
    def __post_init__(self):
        if self.passed:
            self.status_icon = f"{Fore.GREEN}✓{Style.RESET_ALL}"
            self.status_text = f"{Fore.GREEN}PASS{Style.RESET_ALL}"
        else:
            self.status_icon = f"{Fore.RED}✗{Style.RESET_ALL}"
            self.status_text = f"{Fore.RED}FAIL{Style.RESET_ALL}"


@dataclass
class TestSuite:
    """Manages a collection of tests"""
    name: str
    results: List[TestResult] = field(default_factory=list)
    
    def add_result(self, result: TestResult):
        self.results.append(result)
    
    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)
    
    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.passed)
    
    @property
    def total_duration(self) -> float:
        return sum(r.duration for r in self.results)


class EcommerceTester:
    """Main test orchestrator"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.suites: List[TestSuite] = []
        self.start_time = None
        
    def log_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  {text}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        
    def log_info(self, text: str):
        """Print info message"""
        print(f"{Fore.BLUE}  ℹ {text}{Style.RESET_ALL}")
        
    def log_success(self, text: str):
        """Print success message"""
        print(f"{Fore.GREEN}  ✓ {text}{Style.RESET_ALL}")
        
    def log_error(self, text: str):
        """Print error message"""
        print(f"{Fore.RED}  ✗ {text}{Style.RESET_ALL}")
        
    def log_warning(self, text: str):
        """Print warning message"""
        print(f"{Fore.YELLOW}  ⚠ {text}{Style.RESET_ALL}")
        
    async def run_test(self, name: str, test_func) -> TestResult:
        """Execute a test and capture result"""
        start = time.time()
        try:
            details = await test_func()
            duration = time.time() - start
            return TestResult(name=name, passed=True, duration=duration, details=details)
        except Exception as e:
            duration = time.time() - start
            return TestResult(name=name, passed=False, duration=duration, error=str(e))
    
    # ==================== SERVICE HEALTH TESTS ====================
    
    async def test_semantic_health(self) -> str:
        """Test Semantic Engine health"""
        response = await self.client.get(f"{SEMANTIC_URL}/health")
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        data = response.json()
        if data.get("status") != "healthy":
            raise Exception(f"Status: {data.get('status')}")
        return f"Status: {data['status']}, Products: {data.get('products_count', 0)}"
    
    async def test_graph_health(self) -> str:
        """Test Graph Service health via orchestrator"""
        # Check orchestrator health which includes graph status
        response = await self.client.get(f"{ORCHESTRATOR_URL}/health")
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        data = response.json()
        if not data.get("graph_service_connected"):
            raise Exception("Graph service not connected")
        return "Graph service connected"
    
    async def test_orchestrator_health(self) -> str:
        """Test Orchestrator health"""
        response = await self.client.get(f"{ORCHESTRATOR_URL}/health")
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        data = response.json()
        if data.get("status") not in ["healthy", "degraded"]:
            raise Exception(f"Status: {data.get('status')}")
        return f"Status: {data['status']}"
    
    # ==================== PRODUCT INGESTION TESTS ====================
    
    async def test_create_single_product(self) -> str:
        """Test creating a single product through orchestrator"""
        product = TEST_PRODUCTS[0]
        response = await self.client.post(
            f"{ORCHESTRATOR_URL}/api/v1/products",
            json=product
        )
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        data = response.json()
        if not data.get("success"):
            raise Exception(f"Success: {data.get('success')}")
        return f"Product {data['product_id']} created in both services"
    
    async def test_batch_create_products(self) -> str:
        """Test batch creating products"""
        products = TEST_PRODUCTS[1:]  # Skip first one
        response = await self.client.post(
            f"{ORCHESTRATOR_URL}/api/v1/products/batch",
            json=products
        )
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        data = response.json()
        if not data.get("success"):
            raise Exception(f"Success: {data.get('success')}")
        return f"Batch: {data['graph_inserted_count']}/{data['total']} products"
    
    async def test_create_product_missing_id(self) -> str:
        """Test error handling for product without ID"""
        invalid_product = TEST_PRODUCTS[0].copy()
        del invalid_product["id"]
        response = await self.client.post(
            f"{ORCHESTRATOR_URL}/api/v1/products",
            json=invalid_product
        )
        if response.status_code != 400:
            raise Exception(f"Expected 400, got {response.status_code}")
        return "Correctly rejected product without ID"
    
    # ==================== SEARCH TESTS ====================
    
    async def test_search_basic(self) -> str:
        """Test basic search functionality"""
        query = {"query": "Nike running shoes", "limit": 5}
        response = await self.client.post(
            f"{ORCHESTRATOR_URL}/api/v1/search",
            json=query
        )
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        data = response.json()
        recs = data.get("recommendations", [])
        if len(recs) == 0:
            raise Exception("No recommendations returned")
        return f"Found {len(recs)} recommendations"
    
    async def test_search_with_price(self) -> str:
        """Test search with price constraint"""
        query = {"query": "laptop under $3000", "limit": 5}
        response = await self.client.post(
            f"{ORCHESTRATOR_URL}/api/v1/search",
            json=query
        )
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        data = response.json()
        recs = data.get("recommendations", [])
        
        # Check if Cypher was generated
        cypher = data.get("cypher_query", "")
        if not cypher:
            raise Exception("No Cypher query generated")
            
        return f"Found {len(recs)} recommendations, Cypher generated"
    
    async def test_search_electronics(self) -> str:
        """Test search for electronics category"""
        query = {"query": "Sony headphones wireless", "limit": 5}
        response = await self.client.post(
            f"{ORCHESTRATOR_URL}/api/v1/search",
            json=query
        )
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        data = response.json()
        recs = data.get("recommendations", [])
        
        # Check both services contributed
        semantic_count = data.get("semantic_results_count", 0)
        graph_count = data.get("graph_results_count", 0)
        
        return f"Found {len(recs)} recs (Semantic: {semantic_count}, Graph: {graph_count})"
    
    async def test_search_verify_scoring(self) -> str:
        """Test that recommendations have proper scoring"""
        query = {"query": "comfortable running shoes", "limit": 3}
        response = await self.client.post(
            f"{ORCHESTRATOR_URL}/api/v1/search",
            json=query
        )
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        data = response.json()
        recs = data.get("recommendations", [])
        
        if not recs:
            raise Exception("No recommendations")
        
        # Verify scoring fields
        first = recs[0]
        if "semantic_score" not in first:
            raise Exception("Missing semantic_score")
        if "graph_score" not in first:
            raise Exception("Missing graph_score")
        if "combined_score" not in first:
            raise Exception("Missing combined_score")
            
        return f"All scores present: semantic={first['semantic_score']:.3f}, graph={first['graph_score']:.3f}"
    
    async def test_search_different_categories(self) -> str:
        """Test search across different product categories"""
        queries = [
            "running shoes",
            "laptop computer",
            "wireless headphones",
            "athletic footwear"
        ]
        
        results = []
        for q in queries:
            response = await self.client.post(
                f"{ORCHESTRATOR_URL}/api/v1/search",
                json={"query": q, "limit": 3}
            )
            if response.status_code == 200:
                data = response.json()
                results.append(f"'{q}': {len(data.get('recommendations', []))} recs")
        
        return f"Tested {len(results)} categories: {', '.join(results)}"
    
    # ==================== DEBUG INFO TESTS ====================
    
    async def test_debug_info_present(self) -> str:
        """Test that debug info (Cypher + search terms) is returned"""
        query = {"query": "red nike shoes", "limit": 3}
        response = await self.client.post(
            f"{ORCHESTRATOR_URL}/api/v1/search",
            json=query
        )
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        data = response.json()
        
        if "cypher_query" not in data:
            raise Exception("Missing cypher_query in response")
        if "search_terms" not in data:
            raise Exception("Missing search_terms in response")
            
        return f"Cypher: {data['cypher_query'][:50]}..., Terms: '{data['search_terms']}'"
    
    # ==================== MAIN TEST RUNNER ====================
    
    async def run_all_tests(self):
        """Run complete test suite"""
        self.start_time = time.time()
        
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  E-COMMERCE TTS - COMPLETE INTEGRATION TEST SUITE{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"\n  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Orchestrator: {ORCHESTRATOR_URL}")
        print(f"  Semantic Engine: {SEMANTIC_URL}")
        
        # ===== PHASE 1: HEALTH CHECKS =====
        suite1 = TestSuite("Service Health Checks")
        self.log_header("PHASE 1: Service Health Checks")
        
        result = await self.run_test("Orchestrator Health", self.test_orchestrator_health)
        suite1.add_result(result)
        self.print_result(result)
        
        result = await self.run_test("Semantic Engine Health", self.test_semantic_health)
        suite1.add_result(result)
        self.print_result(result)
        
        result = await self.run_test("Graph Service Health", self.test_graph_health)
        suite1.add_result(result)
        self.print_result(result)
        
        self.suites.append(suite1)
        
        # If health checks fail, stop here
        if suite1.failed_count > 0:
            self.log_error("Health checks failed. Stopping tests.")
            await self.print_summary()
            return 1
        
        # ===== PHASE 2: PRODUCT INGESTION =====
        suite2 = TestSuite("Product Ingestion")
        self.log_header("PHASE 2: Product Ingestion")
        
        result = await self.run_test("Create Single Product", self.test_create_single_product)
        suite2.add_result(result)
        self.print_result(result)
        
        result = await self.run_test("Batch Create Products", self.test_batch_create_products)
        suite2.add_result(result)
        self.print_result(result)
        
        result = await self.run_test("Create Product Missing ID (Error)", self.test_create_product_missing_id)
        suite2.add_result(result)
        self.print_result(result)
        
        self.suites.append(suite2)
        
        # Wait for indexing
        self.log_info("Waiting 2 seconds for indexing...")
        await asyncio.sleep(2)
        
        # ===== PHASE 3: SEARCH FUNCTIONALITY =====
        suite3 = TestSuite("Search & Recommendations")
        self.log_header("PHASE 3: Search & Recommendations")
        
        result = await self.run_test("Basic Search", self.test_search_basic)
        suite3.add_result(result)
        self.print_result(result)
        
        result = await self.run_test("Search with Price Filter", self.test_search_with_price)
        suite3.add_result(result)
        self.print_result(result)
        
        result = await self.run_test("Electronics Category Search", self.test_search_electronics)
        suite3.add_result(result)
        self.print_result(result)
        
        result = await self.run_test("Verify Recommendation Scoring", self.test_search_verify_scoring)
        suite3.add_result(result)
        self.print_result(result)
        
        result = await self.run_test("Multi-Category Search", self.test_search_different_categories)
        suite3.add_result(result)
        self.print_result(result)
        
        result = await self.run_test("Debug Info Present", self.test_debug_info_present)
        suite3.add_result(result)
        self.print_result(result)
        
        self.suites.append(suite3)
        
        # Print final summary
        await self.print_summary()
        
        # Return exit code
        total_failed = sum(s.failed_count for s in self.suites)
        return 0 if total_failed == 0 else 1
    
    def print_result(self, result: TestResult):
        """Print a single test result"""
        print(f"\n  {result.status_icon} {result.name}")
        print(f"    Duration: {result.duration:.3f}s")
        if result.details:
            print(f"    {Fore.GREEN}{result.details}{Style.RESET_ALL}")
        if result.error:
            print(f"    {Fore.RED}Error: {result.error}{Style.RESET_ALL}")
    
    async def print_summary(self):
        """Print final test summary"""
        self.log_header("TEST SUMMARY")
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_duration = 0
        
        for suite in self.suites:
            total_tests += len(suite.results)
            total_passed += suite.passed_count
            total_failed += suite.failed_count
            total_duration += suite.total_duration
            
            status_color = Fore.GREEN if suite.failed_count == 0 else Fore.YELLOW if suite.passed_count > 0 else Fore.RED
            print(f"\n  {status_color}{suite.name}{Style.RESET_ALL}")
            print(f"    {Fore.GREEN}✓ Passed: {suite.passed_count}{Style.RESET_ALL}")
            if suite.failed_count > 0:
                print(f"    {Fore.RED}✗ Failed: {suite.failed_count}{Style.RESET_ALL}")
            print(f"    Duration: {suite.total_duration:.3f}s")
        
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"  Total Tests: {total_tests}")
        print(f"  {Fore.GREEN}Passed: {total_passed}{Style.RESET_ALL}")
        print(f"  {Fore.RED}Failed: {total_failed}{Style.RESET_ALL}")
        print(f"  Total Duration: {total_duration:.3f}s")
        print(f"  Overall: {((total_passed/total_tests)*100):.1f}% success rate" if total_tests > 0 else "  Overall: N/A")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        
        if total_failed == 0:
            print(f"\n{Fore.GREEN}  ✓ ALL TESTS PASSED!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}  ✗ {total_failed} TEST(S) FAILED{Style.RESET_ALL}")
            print(f"\n  Failed Tests:")
            for suite in self.suites:
                for result in suite.results:
                    if not result.passed:
                        print(f"    - {suite.name}: {result.name}")
    
    async def close(self):
        """Cleanup"""
        await self.client.aclose()


async def main():
    """Main entry point"""
    tester = EcommerceTester()
    try:
        exit_code = await tester.run_all_tests()
    finally:
        await tester.close()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
