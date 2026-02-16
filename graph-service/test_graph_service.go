package main

import (
	"context"
	"fmt"
	"log"
	"time"

	pb "github.com/navi-prem/ecom-tts/graph-service/api"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

const (
	address = "localhost:50051"
)

// TestResult represents a single test result
type TestResult struct {
	Name      string
	Passed    bool
	Details   string
	Error     string
	Duration  time.Duration
}

// GraphServiceTester handles all tests for the Graph Service
type GraphServiceTester struct {
	client pb.GraphServiceClient
	conn   *grpc.ClientConn
	results []TestResult
}

// NewGraphServiceTester creates a new tester instance
func NewGraphServiceTester() (*GraphServiceTester, error) {
	conn, err := grpc.Dial(address, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, fmt.Errorf("did not connect: %v", err)
	}

	client := pb.NewGraphServiceClient(conn)
	return &GraphServiceTester{
		client: client,
		conn:   conn,
	}, nil
}

// Close closes the gRPC connection
func (t *GraphServiceTester) Close() {
	if t.conn != nil {
		t.conn.Close()
	}
}

// printHeader prints a formatted header
func printHeader(text string) {
	fmt.Println()
	fmt.Println("================================================================================")
	fmt.Printf("  %s\n", text)
	fmt.Println("================================================================================")
}

// printTestResult prints a single test result
func printTestResult(result TestResult) {
	status := "✓ PASS"
	if !result.Passed {
		status = "✗ FAIL"
	}
	
	fmt.Printf("\n  %s %s\n", status, result.Name)
	fmt.Printf("    Duration: %v\n", result.Duration)
	if result.Details != "" {
		fmt.Printf("    %s\n", result.Details)
	}
	if result.Error != "" {
		fmt.Printf("    Error: %s\n", result.Error)
	}
}

// runTest executes a test and records the result
func (t *GraphServiceTester) runTest(name string, testFunc func() (string, error)) bool {
	start := time.Now()
	details, err := testFunc()
	duration := time.Since(start)
	
	result := TestResult{
		Name:     name,
		Passed:   err == nil,
		Details:  details,
		Error:    "",
		Duration: duration,
	}
	
	if err != nil {
		result.Error = err.Error()
	}
	
	t.results = append(t.results, result)
	printTestResult(result)
	
	return result.Passed
}

// ==================== TEST CASES ====================

// TEST 1: CreateProduct - Create Single Product
func (t *GraphServiceTester) testCreateProduct() (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*5)
	defer cancel()
	
	product := &pb.Product{
		Id:          "graph-test-001",
		Name:        "Nike Air Max 90",
		Brand:       "Nike",
		Color:       "Red",
		Price:       129.99,
		OriginalPrice: 159.99,
		Description: "Classic Nike Air Max 90 running shoes",
		Tags:        []string{"running", "athletic"},
		Images:      []string{"https://example.com/image1.jpg"},
		Category: &pb.ProductCategory{
			MainCategory:  "Footwear",
			Subcategory:   "Sneakers",
			SpecificType:  "Running Shoes",
		},
		Sizes: []*pb.ProductSize{
			{
				Size:     "US 8",
				Stock:    10,
				InStock:  true,
				Sku:      "NIKE-AM90-RD-08",
				Variants: []string{"Wide"},
			},
		},
		Attributes: map[string]string{
			"gender":   "Men",
			"material": "Mesh",
		},
	}
	
	req := &pb.CreateProductRequest{Product: product}
	resp, err := t.client.CreateProduct(ctx, req)
	if err != nil {
		return "", fmt.Errorf("CreateProduct failed: %v", err)
	}
	
	if resp.Id != product.Id {
		return "", fmt.Errorf("ID mismatch: expected %s, got %s", product.Id, resp.Id)
	}
	
	return fmt.Sprintf("Created product with ID: %s", resp.Id), nil
}

// TEST 2: GetProduct - Get Product by ID
func (t *GraphServiceTester) testGetProduct() (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*5)
	defer cancel()
	
	req := &pb.GetProductRequest{Id: "graph-test-001"}
	resp, err := t.client.GetProduct(ctx, req)
	if err != nil {
		return "", fmt.Errorf("GetProduct failed: %v", err)
	}
	
	if resp.Product == nil {
		return "", fmt.Errorf("Product not found in response")
	}
	
	if resp.Product.Id != "graph-test-001" {
		return "", fmt.Errorf("ID mismatch: expected graph-test-001, got %s", resp.Product.Id)
	}
	
	return fmt.Sprintf("Retrieved product: %s (Brand: %s)", resp.Product.Name, resp.Product.Brand), nil
}

// TEST 3: GetProduct - Product Not Found
func (t *GraphServiceTester) testGetProductNotFound() (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*5)
	defer cancel()
	
	req := &pb.GetProductRequest{Id: "non-existent-id"}
	resp, err := t.client.GetProduct(ctx, req)
	
	// Expecting an error or empty product
	if err == nil && resp.Product != nil && resp.Product.Id != "" {
		return "", fmt.Errorf("Expected error for non-existent product, but got: %v", resp.Product)
	}
	
	return "Correctly handled non-existent product", nil
}

// TEST 4: UpdateProduct - Update Existing Product
func (t *GraphServiceTester) testUpdateProduct() (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*5)
	defer cancel()
	
	product := &pb.Product{
		Id:          "graph-test-001",
		Name:        "Nike Air Max 90 Updated",
		Brand:       "Nike",
		Color:       "Blue",
		Price:       139.99,
		OriginalPrice: 159.99,
		Description: "Updated description",
		Tags:        []string{"running", "updated"},
		Category: &pb.ProductCategory{
			MainCategory: "Footwear",
			Subcategory:  "Sneakers",
			SpecificType: "Running Shoes",
		},
	}
	
	req := &pb.UpdateProductRequest{Product: product}
	resp, err := t.client.UpdateProduct(ctx, req)
	if err != nil {
		return "", fmt.Errorf("UpdateProduct failed: %v", err)
	}
	
	if !resp.Success {
		return "", fmt.Errorf("Update failed: success=false")
	}
	
	return "Product updated successfully", nil
}

// TEST 5: SearchProducts - Search by Query
func (t *GraphServiceTester) testSearchProducts() (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*5)
	defer cancel()
	
	query := `MATCH (p:Product) WHERE p.brand = 'Nike' RETURN p`
	req := &pb.SearchProductsRequest{Query: query}
	resp, err := t.client.SearchProducts(ctx, req)
	if err != nil {
		return "", fmt.Errorf("SearchProducts failed: %v", err)
	}
	
	return fmt.Sprintf("Found %d products", len(resp.Products)), nil
}

// TEST 6: UpdateStock - Update Product Stock
func (t *GraphServiceTester) testUpdateStock() (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*5)
	defer cancel()
	
	req := &pb.UpdateStockRequest{
		ProductId: "graph-test-001",
		Sku:       "NIKE-AM90-RD-08",
		NewStock:  25,
	}
	resp, err := t.client.UpdateStock(ctx, req)
	if err != nil {
		return "", fmt.Errorf("UpdateStock failed: %v", err)
	}
	
	if !resp.Success {
		return "", fmt.Errorf("Stock update failed: success=false")
	}
	
	return fmt.Sprintf("Stock updated to %d", req.NewStock), nil
}

// TEST 7: DeleteProduct - Delete Product
func (t *GraphServiceTester) testDeleteProduct() (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*5)
	defer cancel()
	
	// First create a product to delete
	product := &pb.Product{
		Id:    "graph-test-delete",
		Name:  "Test Product To Delete",
		Brand: "TestBrand",
		Category: &pb.ProductCategory{
			MainCategory: "Test",
			Subcategory:  "Test",
			SpecificType: "Test",
		},
	}
	
	_, err := t.client.CreateProduct(ctx, &pb.CreateProductRequest{Product: product})
	if err != nil {
		return "", fmt.Errorf("Failed to create product for deletion: %v", err)
	}
	
	// Now delete it
	req := &pb.DeleteProductRequest{Id: "graph-test-delete"}
	resp, err := t.client.DeleteProduct(ctx, req)
	if err != nil {
		return "", fmt.Errorf("DeleteProduct failed: %v", err)
	}
	
	if !resp.Success {
		return "", fmt.Errorf("Delete failed: success=false")
	}
	
	return "Product deleted successfully", nil
}

// TEST 8: Batch Create Products
func (t *GraphServiceTester) testBatchCreate() (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*10)
	defer cancel()
	
	products := []*pb.Product{
		{
			Id:    "graph-batch-001",
			Name:  "Adidas Ultraboost",
			Brand: "Adidas",
			Category: &pb.ProductCategory{
				MainCategory: "Footwear",
				Subcategory:  "Sneakers",
				SpecificType: "Running",
			},
		},
		{
			Id:    "graph-batch-002",
			Name:  "Puma RS-X",
			Brand: "Puma",
			Category: &pb.ProductCategory{
				MainCategory: "Footwear",
				Subcategory:  "Sneakers",
				SpecificType: "Lifestyle",
			},
		},
	}
	
	successCount := 0
	for _, product := range products {
		req := &pb.CreateProductRequest{Product: product}
		resp, err := t.client.CreateProduct(ctx, req)
		if err == nil && resp.Id == product.Id {
			successCount++
		}
	}
	
	if successCount != len(products) {
		return "", fmt.Errorf("Only %d/%d products created", successCount, len(products))
	}
	
	return fmt.Sprintf("Created %d products in batch", successCount), nil
}

// RunAllTests runs all test cases
func (t *GraphServiceTester) RunAllTests() {
	printHeader("GRAPH SERVICE - COMPLETE TEST SUITE")
	fmt.Printf("  Address: %s\n", address)
	fmt.Printf("  Total Tests: 8\n")
	
	tests := []struct {
		name string
		fn   func() (string, error)
	}{
		{"Create Single Product", t.testCreateProduct},
		{"Get Product by ID", t.testGetProduct},
		{"Get Product Not Found", t.testGetProductNotFound},
		{"Update Product", t.testUpdateProduct},
		{"Search Products", t.testSearchProducts},
		{"Update Stock", t.testUpdateStock},
		{"Delete Product", t.testDeleteProduct},
		{"Batch Create Products", t.testBatchCreate},
	}
	
	passed := 0
	failed := 0
	
	for _, test := range tests {
		if t.runTest(test.name, test.fn) {
			passed++
		} else {
			failed++
		}
	}
	
	t.PrintSummary(passed, failed)
}

// PrintSummary prints the test summary
func (t *GraphServiceTester) PrintSummary(passed, failed int) {
	fmt.Println()
	fmt.Println("================================================================================")
	fmt.Println("  TEST SUMMARY")
	fmt.Println("================================================================================")
	fmt.Printf("\n  Total Tests: %d\n", passed+failed)
	fmt.Printf("  Passed: %d\n", passed)
	fmt.Printf("  Failed: %d\n", failed)
	
	if failed == 0 {
		fmt.Println("\n  ✓ ALL TESTS PASSED!")
	} else {
		fmt.Printf("\n  ✗ %d TEST(S) FAILED\n", failed)
	}
}

func main() {
	tester, err := NewGraphServiceTester()
	if err != nil {
		log.Fatalf("Failed to create tester: %v", err)
	}
	defer tester.Close()
	
	tester.RunAllTests()
}
