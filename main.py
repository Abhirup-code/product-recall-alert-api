from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from products import router as products_router
from recalls import router as recalls_router

app = FastAPI(
    title="Product Recall Alert API Application",
    description="Register products and check them against U.S. CPSC recalls.",
)

app.include_router(products_router)
app.include_router(recalls_router)


#  wrong format returns 400 
@app.exception_handler(RequestValidationError)
async def wrong_format(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(part) for part in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(status_code=400, content={"detail": "Wrong format", "errors": errors})


#  415 Unsupported Media Type when POST/PUT is not sent as JSON
@app.middleware("http")
async def require_json(request: Request, call_next):
    if request.method in ("POST", "PUT"):
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            return JSONResponse(
                status_code=415,
                content={"detail": "Unsupported Media Type: send JSON with Content-Type: application/json"},
            )
    return await call_next(request)


#  unexpected error returns 500 
@app.exception_handler(Exception)
async def server_error(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": type(exc).__name__},
    )


# Welcome message in JSON
@app.get("/")
def home():
    return {
        "message": "Welcome to Product Recall Alert API Application",
        "links": [
            {"rel": "products", "href": "/products"},
            {"rel": "recalls", "href": "/recalls?query=crib"},
            {"rel": "docs", "href": "/docs"},
        ],
    }
