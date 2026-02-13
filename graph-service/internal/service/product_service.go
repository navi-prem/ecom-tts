package service

import (
	"context"

	pb "github.com/navi-prem/ecom-tts/graph-service/api"
	"github.com/navi-prem/ecom-tts/graph-service/internal/repository"
)

type ProductService struct {
	pb.UnimplementedGraphServiceServer
	repo *repository.ProductRepository
}

func NewProductService(repo *repository.ProductRepository) *ProductService {
	return &ProductService{repo: repo}
}

func (s *ProductService) CreateProduct(ctx context.Context, req *pb.CreateProductRequest) (*pb.CreateProductResponse, error) {

	err := s.repo.CreateProduct(ctx, req.Product)
	if err != nil {
		return nil, err
	}

	return &pb.CreateProductResponse{
		Id: req.Product.Id,
	}, nil
}

func (s *ProductService) GetProduct(ctx context.Context, req *pb.GetProductRequest) (*pb.GetProductResponse, error) {

	product, err := s.repo.GetProduct(ctx, req.Id)
	if err != nil {
		return nil, err
	}

	return &pb.GetProductResponse{
		Product: product,
	}, nil
}

func (s *ProductService) UpdateProduct(ctx context.Context, req *pb.UpdateProductRequest) (*pb.UpdateProductResponse, error) {

	err := s.repo.UpdateProduct(ctx, req.Product)
	if err != nil {
		return nil, err
	}

	return &pb.UpdateProductResponse{
		Success: true,
	}, nil
}

func (s *ProductService) DeleteProduct(ctx context.Context, req *pb.DeleteProductRequest) (*pb.DeleteProductResponse, error) {

	err := s.repo.DeleteProduct(ctx, req.Id)
	if err != nil {
		return nil, err
	}

	return &pb.DeleteProductResponse{
		Success: true,
	}, nil
}

func (s *ProductService) SearchProducts(ctx context.Context, req *pb.SearchProductsRequest) (*pb.SearchProductsResponse, error) {

	results, err := s.repo.SearchProducts(ctx, req.Query)
	if err != nil {
		return nil, err
	}

	return &pb.SearchProductsResponse{
		Products: results,
	}, nil
}

func (s *ProductService) UpdateStock(ctx context.Context, req *pb.UpdateStockRequest) (*pb.UpdateStockResponse, error) {

	err := s.repo.UpdateStock(ctx, req.Sku, req.NewStock)
	if err != nil {
		return nil, err
	}

	return &pb.UpdateStockResponse{
		Success: true,
	}, nil
}

