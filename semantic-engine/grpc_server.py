from concurrent import futures
import grpc
from typing import List, Dict, Any, Optional
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'proto'))

import product_pb2
import product_pb2_grpc

from app.services.embedding import get_embedding_service, EmbeddingService
from app.services.vector_store import get_vector_store, VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticService(product_pb2_grpc.ProductServiceServicer):
    def __init__(self):
        self.embedding_service: EmbeddingService = get_embedding_service()
        self.vector_store: VectorStore = get_vector_store()
    
    def _product_to_proto(self, product_data: Dict[str, Any]) -> product_pb2.Product:
        """Convert dict to Product protobuf message."""
        category_data = product_data.get("category", {})
        category = product_pb2.ProductCategory(
            main_category=category_data.get("main_category", ""),
            subcategory=category_data.get("subcategory", ""),
            specific_type=category_data.get("specific_type", "")
        )
        
        sizes = []
        for size_data in product_data.get("sizes", []):
            size = product_pb2.ProductSize(
                size=size_data.get("size", ""),
                stock=size_data.get("stock", 0),
                in_stock=size_data.get("in_stock", False),
                variants=size_data.get("variants", []),
                sku=size_data.get("sku", "")
            )
            sizes.append(size)
        
        return product_pb2.Product(
            id=product_data.get("id", ""),
            name=product_data.get("name", ""),
            brand=product_data.get("brand", ""),
            category=category,
            color=product_data.get("color", ""),
            price=float(product_data.get("price", 0)),
            original_price=float(product_data.get("original_price", 0)),
            sizes=sizes,
            tags=product_data.get("tags", []),
            attributes=product_data.get("attributes", {}),
            description=product_data.get("description", ""),
            images=product_data.get("images", [])
        )
    
    def _proto_to_dict(self, product: product_pb2.Product) -> Dict[str, Any]:
        """Convert Product protobuf to dict."""
        return {
            "id": product.id,
            "name": product.name,
            "brand": product.brand,
            "category": {
                "main_category": product.category.main_category,
                "subcategory": product.category.subcategory,
                "specific_type": product.category.specific_type
            } if product.category else {},
            "color": product.color,
            "price": product.price,
            "original_price": product.original_price,
            "sizes": [
                {
                    "size": size.size,
                    "stock": size.stock,
                    "in_stock": size.in_stock,
                    "variants": list(size.variants),
                    "sku": size.sku
                }
                for size in product.sizes
            ],
            "tags": list(product.tags),
            "attributes": dict(product.attributes),
            "description": product.description,
            "images": list(product.images)
        }
    
    def CreateProduct(self, request, context):
        """Create a single product."""
        try:
            product_dict = self._proto_to_dict(request.product)
            
            # Generate embedding
            points = self.embedding_service.embed_products([product_dict])
            
            if not points:
                return product_pb2.CreateProductResponse(
                    id="",
                    success=False,
                    message="Failed to generate embedding"
                )
            
            # Insert to Qdrant
            result = self.vector_store.upsert_products(points)
            
            success = len(result["errors"]) == 0
            return product_pb2.CreateProductResponse(
                id=request.product.id,
                success=success,
                message=f"Successfully added product: {request.product.id}" if success else result["errors"][0]
            )
        except Exception as e:
            logger.error(f"Failed to create product: {e}")
            return product_pb2.CreateProductResponse(
                id="",
                success=False,
                message=str(e)
            )
    
    def GetProduct(self, request, context):
        """Get a product by ID."""
        try:
            product = self.vector_store.get_product(request.id)
            if product and product.get("payload"):
                payload = product["payload"]
                product_proto = self._product_to_proto(payload)
                return product_pb2.GetProductResponse(
                    product=product_proto,
                    found=True
                )
            return product_pb2.GetProductResponse(found=False)
        except Exception as e:
            logger.error(f"Failed to get product: {e}")
            return product_pb2.GetProductResponse(found=False)
    
    def UpdateProduct(self, request, context):
        """Update a product."""
        try:
            product_dict = self._proto_to_dict(request.product)
            
            # Generate embedding
            points = self.embedding_service.embed_products([product_dict])
            
            if not points:
                return product_pb2.UpdateProductResponse(
                    success=False,
                    message="Failed to generate embedding"
                )
            
            # Upsert to Qdrant
            result = self.vector_store.upsert_products(points)
            
            success = len(result["errors"]) == 0
            return product_pb2.UpdateProductResponse(
                success=success,
                message=f"Successfully updated product: {request.product.id}" if success else result["errors"][0]
            )
        except Exception as e:
            logger.error(f"Failed to update product: {e}")
            return product_pb2.UpdateProductResponse(
                success=False,
                message=str(e)
            )
    
    def DeleteProduct(self, request, context):
        """Delete a product."""
        try:
            success = self.vector_store.delete_product(request.id)
            return product_pb2.DeleteProductResponse(
                success=success,
                message=f"Product {request.id} deleted" if success else f"Product {request.id} not found"
            )
        except Exception as e:
            logger.error(f"Failed to delete product: {e}")
            return product_pb2.DeleteProductResponse(
                success=False,
                message=str(e)
            )
    
    def CreateProductsBatch(self, request, context):
        """Create multiple products in batch."""
        try:
            products = [self._proto_to_dict(p) for p in request.products]
            
            # Generate embeddings
            points = self.embedding_service.embed_products(products)
            
            if not points:
                return product_pb2.CreateProductsBatchResponse(
                    inserted_count=0,
                    total=len(products),
                    success=False,
                    message="Failed to generate embeddings"
                )
            
            # Insert to Qdrant
            result = self.vector_store.upsert_products(points)
            
            success = len(result["errors"]) == 0
            return product_pb2.CreateProductsBatchResponse(
                inserted_count=result["inserted"],
                total=len(products),
                success=success,
                message=f"Successfully inserted {result['inserted']}/{len(products)} products",
                failed_ids=[]
            )
        except Exception as e:
            logger.error(f"Failed to batch insert products: {e}")
            return product_pb2.CreateProductsBatchResponse(
                inserted_count=0,
                total=len(request.products),
                success=False,
                message=str(e),
                failed_ids=[p.id for p in request.products]
            )
    
    def SemanticSearch(self, request, context):
        """Search products using semantic similarity."""
        try:
            # Generate query embedding
            query_vector = self.embedding_service.embed_query(request.query)
            
            # Build filters
            filters = dict(request.filters) if request.filters else None
            
            # Search in Qdrant
            results = self.vector_store.search(
                query_vector=query_vector,
                limit=request.limit,
                filters=filters,
                min_score=request.min_score
            )
            
            # Format results
            search_results = []
            for point in results:
                payload = point.payload or {}
                product_proto = self._product_to_proto(payload)
                search_results.append(product_pb2.SearchResult(
                    product=product_proto,
                    score=point.score,
                    source="semantic"
                ))
            
            return product_pb2.SearchProductsResponse(
                results=search_results,
                total=len(search_results),
                query=request.query
            )
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return product_pb2.SearchProductsResponse(
                results=[],
                total=0,
                query=request.query
            )
    
    def SearchProducts(self, request, context):
        """Alias for SemanticSearch to maintain unified interface."""
        # Convert SearchProductsRequest to SemanticSearchRequest
        semantic_request = product_pb2.SemanticSearchRequest(
            query=request.query,
            limit=request.limit,
            filters=request.filters,
            min_score=0.3
        )
        return self.SemanticSearch(semantic_request, context)
    
    def Health(self, request, context):
        """Health check."""
        try:
            count = self.vector_store.count()
            return product_pb2.HealthResponse(
                status="healthy",
                products_count=count,
                database_connected=True,
                service_name="semantic-engine"
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return product_pb2.HealthResponse(
                status="unhealthy",
                products_count=0,
                database_connected=False,
                service_name="semantic-engine"
            )


def serve(port=50052):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    product_pb2_grpc.add_ProductServiceServicer_to_server(SemanticService(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info(f"Semantic Service gRPC server started on port {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    import os
    port = int(os.getenv("SEMANTIC_SERVICE_PORT", "50052"))
    serve(port)
