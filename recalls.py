#CPSC recall search
# Calls the public CPSC recalls API  converts each record


import httpx
from cachetools import TTLCache
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

CPSC_URL = "https://www.saferproducts.gov/RestWebServices/Recall"
TIMEOUT_SECONDS = 15

# Cacheu max 200 searchesup to 3 hours
recall_cache = TTLCache(maxsize=200, ttl=3 * 60 * 60)


# Recall model with Pydantic
class Recall(BaseModel):
    recall_id: Optional[int] = None
    recall_number: Optional[str] = None
    title: str
    date: Optional[str] = None
    hazard: Optional[str] = None
    remedy: Optional[str] = None
    products: list[str] = []
    manufacturers: list[str] = []
    url: Optional[str] = None


# Pull Name value from  CPSC list field
def _names(items):
    return [item["Name"] for item in (items or []) if isinstance(item, dict) and item.get("Name")]


# Convert  raw CPSC record to Recall model
def to_recall(raw: dict) -> Recall:
    hazards = _names(raw.get("Hazards"))
    remedies = _names(raw.get("Remedies"))
    date = raw.get("RecallDate")
    return Recall(
        recall_id=raw.get("RecallID"),
        recall_number=raw.get("RecallNumber"),
        title=raw.get("Title") or "Untitled recall",
        date=date[:10] if date else None,
        hazard="; ".join(hazards) or None,
        remedy="; ".join(remedies) or None,
        products=_names(raw.get("Products")),
        manufacturers=_names(raw.get("Manufacturers")),
        url=raw.get("URL"),
    )



#   from recalls import fetch_recalls
#   recalls = fetch_recalls(product.name)
def fetch_recalls(product_name: str) -> list[Recall]:
    key = product_name.strip().lower()

    # Return cached result
    if key in recall_cache:
        return recall_cache[key]

    try:
        response = httpx.get(
            CPSC_URL,
            params={"ProductName": key, "format": "json"},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="CPSC recall service timed out. Try again later.")
    except (httpx.HTTPError, ValueError):
        raise HTTPException(status_code=502, detail="CPSC recall service is unavailable. Try again later.")

    if not isinstance(data, list):
        raise HTTPException(status_code=502, detail="CPSC recall service returned unexpected data.")

    recalls = [to_recall(item) for item in data if isinstance(item, dict)]
    recalls.sort(key=lambda r: r.date or "", reverse=True)  # newest first

    recall_cache[key] = recalls
    return recalls


# FastAPI router for recall endpoints
router = APIRouter(tags=["Recalls (utility service wrapping CPSC)"])


# Search CPSC recalls directly
@router.get("/recalls")
def search_recalls(
    query: str = Query(min_length=2, description="Product name to search, e.g. crib"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
):
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    results = fetch_recalls(query)
    page = results[offset:offset + limit]
    response = {
        "query": query,
        "total_found": len(results),
        "offset": offset,
        "returned": len(page),
        "recalls": page,
        "links": [{"rel": "self", "href": f"/recalls?query={query}&offset={offset}&limit={limit}"}],
    }
    # HATEOAS link to next page when there is one
    if offset + limit < len(results):
        response["links"].append(
            {"rel": "next", "href": f"/recalls?query={query}&offset={offset + limit}&limit={limit}"}
        )
    return response
