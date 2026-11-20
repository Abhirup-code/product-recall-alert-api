from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, HTTPException, Query
import json
from pathlib import Path
from typing import Optional

# Product model with Pydantic
class Product(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    brand: str
    category: str
    model_number: str

    #  product name cannot be empty check
    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value.strip():
            raise ValueError("Product name cannot be empty")
        return value


# Memory db  store products in JSON file
DATA_FILE = Path(__file__).resolve().parent / "products.json"

# Load products from JSON file to memory
def load_products():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as file:
            data = json.load(file)
            return [Product(**item) for item in data]

    return []

products_db = load_products()


# From POST/products saved in JSON dbe file
def save_products():
    with open(DATA_FILE, "w") as file:
        json.dump(
            [product.model_dump() for product in products_db],
            file,
            indent=4
        )

# HATEOAS links to client can find related resources from the response itself
def with_links(product: Product) -> dict:
    data = product.model_dump()
    data["links"] = [
        {"rel": "self", "href": f"/products/{product.id}"},
        {"rel": "all-products", "href": "/products"},
    ]
    return data


# FastAPI router for productendpoints
router = APIRouter(tags=["Products (entity service)"])


@router.post("/products", status_code=201)
def add_product(product: Product):
    # Checking whetherproduct ID exists:
    for existing_product in products_db:
        if existing_product.id == product.id:
            raise HTTPException(
                status_code=409,
                detail="Product ID already exists"
            )

    # Adding product to db
    products_db.append(product)
    save_products() #in JSON file

    return {
        "message": "Product added successfully",
        "product": with_links(product)
    }


# Resource URI for the collection with filtering 

@router.get("/products")
def get_products(
    category: Optional[str] = Query(None, description="Only products in this category"),
    brand: Optional[str] = Query(None, description="Only products of this brand"),
    offset: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max products to return"),
):
    matching = [
        p for p in products_db
        if (category is None or p.category.lower() == category.lower())
        and (brand is None or p.brand.lower() == brand.lower())
    ]
    page = matching[offset:offset + limit]
    return {
        "total": len(matching),
        "offset": offset,
        "limit": limit,
        "products": [with_links(p) for p in page],
    }


# Old URI kept
@router.get("/All", include_in_schema=False)
def get_products_old():
    return products_db


#Getting product by ID
@router.get("/products/{product_id}")
def get_product(product_id: int):

    for product in products_db:
        if product.id == product_id:
            return with_links(product)

    raise HTTPException(
        status_code=404,
        detail="Product not found"
    )


# Updateing existing product by ID
@router.put("/products/{product_id}")
def update_product(product_id: int, updated_product: Product):
    for index, product in enumerate(products_db):
        if product.id == product_id:

            # Keeping existing product ID - primary key not changed
            if updated_product.id != product_id:
                raise HTTPException(
                    status_code=400,
                    detail="Product ID cannot be changed"
                )

            # Update product
            products_db[index] = updated_product

            # Save changes to products.json
            save_products()

            return {
                "message": "Product updated successfully",
                "product": with_links(updated_product)
            }

    raise HTTPException(
        status_code=404,
        detail="Product not found"
    )


# Delete product by ID
@router.delete("/products/{product_id}")
def delete_product(product_id: int):
    for product in products_db:
        if product.id == product_id:

            # Remove the product from db
            products_db.remove(product)

            # Save  updated list to products.json
            save_products()

            return {
                "message": "Product deleted successfully",
                "deleted_product": product
            }

    raise HTTPException(
        status_code=404,
        detail="Product not found"
    )
