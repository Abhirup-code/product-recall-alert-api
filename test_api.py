# Tests for products and serror handling run with pytest -v


import pytest
from fastapi.testclient import TestClient

import products
import recalls
from main import app

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setattr(products, "save_products", lambda: None)
    products.products_db[:] = [
        products.Product(id=1, name="Crib", brand="Graco", category="Baby", model_number="G1"),
        products.Product(id=2, name="Toaster", brand="Prestige", category="Kitchen", model_number="T1"),
    ]


def test_post_returns_201_with_links():
    r = client.post("/products", json={"id": 3, "name": "Kettle", "brand": "X",
                                       "category": "Kitchen", "model_number": "K1"})
    assert r.status_code == 201
    assert {"rel": "self", "href": "/products/3"} in r.json()["product"]["links"]


def test_post_duplicate_returns_409():
    r = client.post("/products", json={"id": 1, "name": "A", "brand": "B",
                                       "category": "C", "model_number": "D"})
    assert r.status_code == 409


def test_list_products_with_offset_limit():
    body = client.get("/products", params={"offset": 1, "limit": 1}).json()
    assert body["total"] == 2
    assert [p["id"] for p in body["products"]] == [2]


def test_get_put_delete():
    assert client.get("/products/1").status_code == 200
    assert client.get("/products/99").status_code == 404
    updated = {"id": 1, "name": "Crib", "brand": "Graco", "category": "Baby", "model_number": "G2"}
    assert client.put("/products/1", json=updated).status_code == 200
    assert client.put("/products/1", json={**updated, "id": 5}).status_code == 400
    assert client.delete("/products/2").status_code == 200
    assert client.delete("/products/2").status_code == 404


def test_root_lists_links():
    rels = [l["rel"] for l in client.get("/").json()["links"]]
    assert rels == ["products", "recalls", "docs"]


def test_unexpected_error_returns_json_500(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("bug")
    monkeypatch.setattr(recalls.httpx, "get", boom)
    recalls.recall_cache.clear()
    r = client.get("/recalls", params={"query": "crib"})
    assert r.status_code == 500
    assert r.json()["detail"] == "Internal server error"


def test_wrong_format_returns_400():
    r = client.post("/products", json={"id": 9, "name": ""})
    assert r.status_code == 400
    assert r.json()["detail"] == "Wrong format"


def test_non_json_returns_415():
    r = client.post("/products", content="id=9", headers={"Content-Type": "text/plain"})
    assert r.status_code == 415


def test_filter_by_category_and_brand():
    body = client.get("/products", params={"category": "kitchen"}).json()
    assert [p["id"] for p in body["products"]] == [2]
    body = client.get("/products", params={"brand": "graco"}).json()
    assert [p["id"] for p in body["products"]] == [1]
