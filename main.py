from fastapi import FastAPI
from products import router as products_router

app = FastAPI(title="Product Recall Alert API Application")

app.include_router(products_router)

# Welcome message in JSON:
@app.get("/")
def home():
    return {"message": "Welcome to Product Recall Alert API Application"}
