package repository

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"

	pb "github.com/navi-prem/ecom-tts/graph-service/api"
	"github.com/neo4j/neo4j-go-driver/v5/neo4j"
)

type ProductRepository struct {
	driver neo4j.DriverWithContext
}

func NewProductRepository(driver neo4j.DriverWithContext) *ProductRepository {
	return &ProductRepository{driver: driver}
}

func (r *ProductRepository) CreateProduct(ctx context.Context, p *pb.Product) error {
	// Validate required fields
	if p.Id == "" {
		return errors.New("product id is required")
	}
	if p.Name == "" {
		return errors.New("product name is required")
	}
	if p.Brand == "" {
		return errors.New("product brand is required")
	}

	session := r.driver.NewSession(ctx, neo4j.SessionConfig{AccessMode: neo4j.AccessModeWrite})
	defer session.Close(ctx)

	// Serialize attributes to JSON string
	attributesJSON, err := json.Marshal(p.Attributes)
	if err != nil {
		return fmt.Errorf("failed to serialize attributes: %w", err)
	}

	_, err = session.ExecuteWrite(ctx, func(tx neo4j.ManagedTransaction) (any, error) {

		// Create Product
		_, err := tx.Run(ctx, `
			CREATE (p:Product {
				id: $id,
				name: $name,
				brand: $brand,
				color: $color,
				price: $price,
				original_price: $original_price,
				description: $description,
				tags: $tags,
				images: $images,
				attributes: $attributes
			})
		`, map[string]any{
			"id":             p.Id,
			"name":           p.Name,
			"brand":          p.Brand,
			"color":          p.Color,
			"price":          p.Price,
			"original_price": p.OriginalPrice,
			"description":    p.Description,
			"tags":           p.Tags,
			"images":         p.Images,
			"attributes":     string(attributesJSON),
		})
		if err != nil {
			return nil, err
		}

		// Category
		_, err = tx.Run(ctx, `
			MATCH (p:Product {id: $id})
			MERGE (c:Category {
				main_category: $main_category,
				subcategory: $subcategory,
				specific_type: $specific_type
			})
			MERGE (p)-[:BELONGS_TO]->(c)
		`, map[string]any{
			"id":            p.Id,
			"main_category": p.Category.MainCategory,
			"subcategory":   p.Category.Subcategory,
			"specific_type": p.Category.SpecificType,
		})
		if err != nil {
			return nil, err
		}

		// Sizes
		for _, size := range p.Sizes {
			_, err := tx.Run(ctx, `
				MATCH (p:Product {id: $id})
				CREATE (s:Size {
					sku: $sku,
					size: $size,
					stock: $stock,
					in_stock: $in_stock,
					variants: $variants
				})
				MERGE (p)-[:HAS_SIZE]->(s)
			`, map[string]any{
				"id":       p.Id,
				"sku":      size.Sku,
				"size":     size.Size,
				"stock":    size.Stock,
				"in_stock": size.InStock,
				"variants": size.Variants,
			})
			if err != nil {
				return nil, err
			}
		}

		return nil, nil
	})

	return err
}

func (r *ProductRepository) GetProduct(ctx context.Context, id string) (*pb.Product, error) {
	if id == "" {
		return nil, errors.New("product id is required")
	}

	session := r.driver.NewSession(ctx, neo4j.SessionConfig{AccessMode: neo4j.AccessModeRead})
	defer session.Close(ctx)

	result, err := session.ExecuteRead(ctx, func(tx neo4j.ManagedTransaction) (any, error) {

		res, err := tx.Run(ctx, `
			MATCH (p:Product {id: $id})
			OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)
			OPTIONAL MATCH (p)-[:HAS_SIZE]->(s:Size)
			RETURN p, c, collect(s) as sizes
		`, map[string]any{"id": id})
		if err != nil {
			return nil, err
		}

		if !res.Next(ctx) {
			return nil, errors.New("product not found")
		}

		record := res.Record()

		pNode := record.Values[0].(neo4j.Node)
		cNode, _ := record.Values[1].(neo4j.Node)
		sizesList, _ := record.Values[2].([]interface{})

		var product pb.Product

		props := pNode.Props
		product.Id = getString(props, "id")
		product.Name = getString(props, "name")
		product.Brand = getString(props, "brand")
		product.Color = getString(props, "color")
		if price, ok := props["price"].(float64); ok {
			product.Price = price
		}
		if origPrice, ok := props["original_price"].(float64); ok {
			product.OriginalPrice = origPrice
		}
		product.Description = getString(props, "description")

		if tags, ok := props["tags"].([]interface{}); ok {
			for _, tag := range tags {
				if str, ok := tag.(string); ok {
					product.Tags = append(product.Tags, str)
				}
			}
		}

		if images, ok := props["images"].([]interface{}); ok {
			for _, img := range images {
				if str, ok := img.(string); ok {
					product.Images = append(product.Images, str)
				}
			}
		}

		if attrsStr, ok := props["attributes"].(string); ok {
			product.Attributes = make(map[string]string)
			json.Unmarshal([]byte(attrsStr), &product.Attributes)
		}

		if cNode.Props != nil {
			product.Category = &pb.ProductCategory{
				MainCategory:  getString(cNode.Props, "main_category"),
				Subcategory:   getString(cNode.Props, "subcategory"),
				SpecificType:  getString(cNode.Props, "specific_type"),
			}
		}

		for _, sizeItem := range sizesList {
			if sizeNode, ok := sizeItem.(neo4j.Node); ok {
				sProps := sizeNode.Props
				size := &pb.ProductSize{
					Sku:     getString(sProps, "sku"),
					Size:    getString(sProps, "size"),
				}
				if stock, ok := sProps["stock"].(int64); ok {
					size.Stock = int32(stock)
				}
				if inStock, ok := sProps["in_stock"].(bool); ok {
					size.InStock = inStock
				}
				if variants, ok := sProps["variants"].([]interface{}); ok {
					for _, v := range variants {
						if str, ok := v.(string); ok {
							size.Variants = append(size.Variants, str)
						}
					}
				}
				product.Sizes = append(product.Sizes, size)
			}
		}

		return &product, nil
	})

	if err != nil {
		return nil, err
	}

	return result.(*pb.Product), nil
}

func (r *ProductRepository) UpdateProduct(ctx context.Context, p *pb.Product) error {

	session := r.driver.NewSession(ctx, neo4j.SessionConfig{AccessMode: neo4j.AccessModeWrite})
	defer session.Close(ctx)

	// Serialize attributes to JSON string
	attributesJSON, err := json.Marshal(p.Attributes)
	if err != nil {
		return fmt.Errorf("failed to serialize attributes: %w", err)
	}

	_, err = session.ExecuteWrite(ctx, func(tx neo4j.ManagedTransaction) (any, error) {

		_, err := tx.Run(ctx, `
			MATCH (p:Product {id: $id})
			SET p.name = $name,
				p.brand = $brand,
				p.color = $color,
				p.price = $price,
				p.original_price = $original_price,
				p.description = $description,
				p.tags = $tags,
				p.images = $images,
				p.attributes = $attributes
		`, map[string]any{
			"id":             p.Id,
			"name":           p.Name,
			"brand":          p.Brand,
			"color":          p.Color,
			"price":          p.Price,
			"original_price": p.OriginalPrice,
			"description":    p.Description,
			"tags":           p.Tags,
			"images":         p.Images,
			"attributes":     string(attributesJSON),
		})
		return nil, err
	})

	return err
}

func (r *ProductRepository) DeleteProduct(ctx context.Context, id string) error {
	if id == "" {
		return errors.New("product id is required")
	}

	session := r.driver.NewSession(ctx, neo4j.SessionConfig{AccessMode: neo4j.AccessModeWrite})
	defer session.Close(ctx)

	_, err := session.ExecuteWrite(ctx, func(tx neo4j.ManagedTransaction) (any, error) {
		_, err := tx.Run(ctx, `
			MATCH (p:Product {id: $id})
			DETACH DELETE p
		`, map[string]any{"id": id})
		return nil, err
	})

	return err
}

func (r *ProductRepository) UpdateStock(ctx context.Context, sku string, stock int32) error {
	if sku == "" {
		return errors.New("sku is required")
	}

	session := r.driver.NewSession(ctx, neo4j.SessionConfig{AccessMode: neo4j.AccessModeWrite})
	defer session.Close(ctx)

	_, err := session.ExecuteWrite(ctx, func(tx neo4j.ManagedTransaction) (any, error) {
		_, err := tx.Run(ctx, `
			MATCH (s:Size {sku: $sku})
			SET s.stock = $stock,
				s.in_stock = CASE WHEN $stock > 0 THEN true ELSE false END
		`, map[string]any{
			"sku":   sku,
			"stock": stock,
		})
		return nil, err
	})

	return err
}

// Helper
func getString(props map[string]any, key string) string {
	if val, ok := props[key]; ok {
		if str, ok := val.(string); ok {
			return str
		}
	}
	return ""
}

// validateCypherQuery checks if the query is safe to execute
func validateCypherQuery(query string) error {
	// Convert to uppercase for case-insensitive checking
	upperQuery := strings.ToUpper(query)
	
	// List of dangerous Cypher keywords that should be blocked
	dangerousKeywords := []string{
		"CREATE", "MERGE", "DELETE", "DETACH", "DROP", "REMOVE", "SET",
		"CALL", "LOAD", "UNWIND", "FOREACH", "APOC", "GDS",
	}
	
	for _, keyword := range dangerousKeywords {
		if strings.Contains(upperQuery, keyword) {
			return fmt.Errorf("unsafe query: contains forbidden keyword '%s'", keyword)
		}
	}
	
	// Ensure query starts with MATCH
	trimmed := strings.TrimSpace(upperQuery)
	if !strings.HasPrefix(trimmed, "MATCH") {
		return fmt.Errorf("unsafe query: must start with MATCH")
	}
	
	// Ensure query contains RETURN
	if !strings.Contains(upperQuery, "RETURN") {
		return fmt.Errorf("unsafe query: must contain RETURN clause")
	}
	
	return nil
}

/*
NEED TO RUN ONCE

CREATE FULLTEXT INDEX productSearch
FOR (p:Product)
ON EACH [p.name, p.description, p.brand]
*/
func (r *ProductRepository) SearchProducts(
    ctx context.Context,
    queryStr string,
) ([]*pb.Product, error) {
    // Validate the query for safety
    if err := validateCypherQuery(queryStr); err != nil {
        return nil, err
    }

    session := r.driver.NewSession(ctx, neo4j.SessionConfig{
        AccessMode: neo4j.AccessModeRead,
    })
    defer session.Close(ctx)

    result, err := session.ExecuteRead(ctx,
        func(tx neo4j.ManagedTransaction) (any, error) {

            res, err := tx.Run(ctx, queryStr, nil)
            if err != nil {
                return nil, err
            }

            var products []*pb.Product

            for res.Next(ctx) {
                record := res.Record()

                // Expect AI to return: RETURN p
                nodeValue, ok := record.Get("p")
                if !ok {
                    continue
                }

                node, ok := nodeValue.(neo4j.Node)
                if !ok {
                    continue
                }

                props := node.Props

                product := &pb.Product{
                    Id:          getString(props, "id"),
                    Name:        getString(props, "name"),
                    Brand:       getString(props, "brand"),
                    Description: getString(props, "description"),
                }

                products = append(products, product)
            }

            return products, nil
        })

    if err != nil {
        return nil, err
    }

    return result.([]*pb.Product), nil
}
