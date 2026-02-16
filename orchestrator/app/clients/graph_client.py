import grpc
from typing import List, Dict, Any, Optional
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import graph_pb2
import graph_pb2_grpc

logger = logging.getLogger(__name__)


class GraphServiceClient:
    def __init__(self, target: str = "localhost:50051"):
        self.target = target
        self.channel = None
        self.stub = None
    
    def connect(self):
        try:
            self.channel = grpc.insecure_channel(self.target)
            self.stub = graph_pb2_grpc.GraphServiceStub(self.channel)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to graph service: {e}")
            return False
    
    def health_check(self) -> bool:
        try:
            if not self.stub:
                self.connect()
            if self.channel is None:
                return False
            grpc.channel_ready_future(self.channel).result(timeout=2)
            return True
        except Exception as e:
            logger.error(f"Graph service health check failed: {e}")
            return False
    
    def _build_product(self, product_data: Dict[str, Any]) -> graph_pb2.Product:
        category_data = product_data.get("category", {})
        category = graph_pb2.ProductCategory(
            main_category=category_data.get("main_category", ""),
            subcategory=category_data.get("subcategory", ""),
            specific_type=category_data.get("specific_type", "")
        )
        
        sizes = []
        for size_data in product_data.get("sizes", []):
            size = graph_pb2.ProductSize(
                size=size_data.get("size", ""),
                stock=size_data.get("stock", 0),
                in_stock=size_data.get("in_stock", False),
                variants=size_data.get("variants", []),
                sku=size_data.get("sku", "")
            )
            sizes.append(size)
        
        attributes = product_data.get("attributes", {})
        
        return graph_pb2.Product(
            id=product_data.get("id", ""),
            name=product_data.get("name", ""),
            brand=product_data.get("brand", ""),
            category=category,
            color=product_data.get("color", ""),
            price=float(product_data.get("price", 0)),
            original_price=float(product_data.get("original_price", 0)),
            sizes=sizes,
            tags=product_data.get("tags", []),
            attributes=attributes,
            description=product_data.get("description", ""),
            images=product_data.get("images", [])
        )
    
    def search_products(self, cypher_query: str) -> List[Dict[str, Any]]:
        """Execute raw Cypher query on Graph Service."""
        try:
            if not self.stub:
                self.connect()
            
            request = graph_pb2.SearchProductsRequest(query=cypher_query)
            response = self.stub.SearchProducts(request)
            
            results = []
            for product in response.products:
                results.append({
                    "id": product.id,
                    "name": product.name,
                    "brand": product.brand,
                    "price": product.price,
                    "original_price": product.original_price,
                    "color": product.color,
                    "description": product.description,
                    "category": {
                        "main_category": product.category.main_category,
                        "subcategory": product.category.subcategory,
                        "specific_type": product.category.specific_type
                    } if product.category else None,
                    "tags": list(product.tags),
                    "sizes": [
                        {
                            "size": size.size,
                            "stock": size.stock,
                            "in_stock": size.in_stock,
                            "sku": size.sku,
                            "variants": list(size.variants)
                        }
                        for size in product.sizes
                    ]
                })
            return results
        except Exception as e:
            logger.error(f"Graph search failed: {e}")
            return []
    
    def create_product(self, product_data: Dict[str, Any]) -> Optional[str]:
        try:
            if not self.stub:
                self.connect()
            
            product = self._build_product(product_data)
            request = graph_pb2.CreateProductRequest(product=product)
            response = self.stub.CreateProduct(request)
            return response.id
        except Exception as e:
            logger.error(f"Failed to create product in graph: {e}")
            return None
    
    def close(self):
        if self.channel:
            self.channel.close()
