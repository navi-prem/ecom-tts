(:Product {id, name, brand, color, price, original_price, description, tags, images, attributes})

(:Category {main_category, subcategory, specific_type})

(:Size {sku, size, stock, in_stock, variants})

Relationships:
(:Product)-[:BELONGS_TO]->(:Category)
(:Product)-[:HAS_SIZE]->(:Size)
