from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, HTTPException
import json
from pathlib import Path

# Product model using Pydantic:
class Product(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    brand: str
    category: str
    model_number: str

    # Customization of the product name cannot be empty using a validator:
    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value.strip():
            raise ValueError("Product name cannot be empty")
        return value


# Memory database to store products in JSON format:
DATA_FILE = Path(__file__).resolve().parent / "products.json"

# Loading products from the JSON file into memory:
def load_products():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as file:
            data = json.load(file)
            return [Product(**item) for item in data]

    return []

products_db = load_products()


# From POST/products saved in JSON database file:
def save_products():
    with open(DATA_FILE, "w") as file:
        json.dump(
            [product.model_dump() for product in products_db],
            file,
            indent=4
        )

# FastAPI router for product-related endpoints:
router = APIRouter()


@router.post("/products", status_code=201)
def add_product(product: Product):
    # Checking whetherproduct ID exists:
    for existing_product in products_db:
        if existing_product.id == product.id:
            raise HTTPException(
                status_code=409,
                detail="Product ID already exists"
            )

    # Adding the product to database:
    products_db.append(product)
    save_products() #in JSON file

    return {
        "message": "Product added successfully",
        "product": product
    }


@router.get("/All")
def get_products():
    return products_db


#Getting a product by ID:
@router.get("/products/{product_id}")
def get_product(product_id: int):

    for product in products_db:
        if product.id == product_id:
            return product

    raise HTTPException(
        status_code=404,
        detail="Product not found"
    )


# Update an existing product by ID:
@router.put("products/{product_id}")
def update_product(product_id: int, updated_product: Product):
    for index, product in enumerate(products_db):
        if product.id == product_id:

            # Keep the existing product ID - primary key should not be changed:
            if updated_product.id != product_id:
                raise HTTPException(
                    status_code=400,
                    detail="Product ID cannot be changed"
                )

            # Update the product:
            products_db[index] = updated_product

            # Save changes to products.json:
            save_products()

            return {
                "message": "Product updated successfully",
                "product": updated_product
            }

    raise HTTPException(
        status_code=404,
        detail="Product not found"
    )


# Delete a product by ID:
@router.delete("products/{product_id}")
def delete_product(product_id: int):
    for product in products_db:
        if product.id == product_id:

            # Remove the product from the in-memory database:
            products_db.remove(product)

            # Save the updated list to products.json:
            save_products()

            return {
                "message": "Product deleted successfully",
                "deleted_product": product
            }

    raise HTTPException(
        status_code=404,
        detail="Product not found"
    )
