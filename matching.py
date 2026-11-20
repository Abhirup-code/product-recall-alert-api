# Recall matching and alerts (Member 3)
# Matches registered products against live CPSC recalls:
#   1. search CPSC by the product name (uses fetch_recalls from recalls.py)
#   2. keep only recalls that mention the product's brand

from fastapi import APIRouter, HTTPException

from products import Product, products_db
from recalls import Recall, fetch_recalls


# Does this recall mention the brand? Checks manufacturers, product names and title
def brand_matches(recall: Recall, brand: str) -> bool:
    brand = brand.strip().lower()
    if not brand:
        return False
    text = " ".join(recall.manufacturers + recall.products + [recall.title]).lower()
    return brand in text


# Matching logic: search by product name, then filter by brand
def match_recalls(product: Product) -> list[Recall]:
    found = fetch_recalls(product.name)
    return [r for r in found if brand_matches(r, product.brand)]


# Find a product by id or return 404 as JSON
def find_product(product_id: int) -> Product:
    for product in products_db:
        if product.id == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")


router = APIRouter(tags=["Matching and alerts (task service)"])


# Recalls matching one product
@router.get("/products/{product_id}/recalls")
def get_product_recalls(product_id: int):
    product = find_product(product_id)
    matches = match_recalls(product)
    return {
        "product": product,
        "recalled": len(matches) > 0,
        "total_matches": len(matches),
        "recalls": matches,
        "links": [
            {"rel": "self", "href": f"/products/{product_id}/recalls"},
            {"rel": "product", "href": f"/products/{product_id}"},
            {"rel": "alerts", "href": "/alerts"},
        ],
    }


# All registered products that have a matching recall
@router.get("/alerts")
def get_alerts():
    alerts = []
    for product in products_db:
        matches = match_recalls(product)
        if matches:
            alerts.append({
                "product": product,
                "total_matches": len(matches),
                "recalls": matches,
                "links": [{"rel": "product-recalls", "href": f"/products/{product.id}/recalls"}],
            })
    return {
        "products_checked": len(products_db),
        "products_recalled": len(alerts),
        "alerts": alerts,
        "links": [{"rel": "self", "href": "/alerts"}, {"rel": "products", "href": "/products"}],
    }
