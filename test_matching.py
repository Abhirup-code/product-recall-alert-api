# Tests for matching and alerts (Member 3) - run with pytest -v
# CPSC is faked so tests run offline and never change products.json

import httpx
import pytest
from fastapi.testclient import TestClient

import products
import recalls
from main import app

client = TestClient(app, raise_server_exceptions=False)

FAKE_CPSC = [
    {
        "RecallID": 1, "RecallNumber": "25001", "Title": "Graco Cribs Recalled Due to Fall Hazard",
        "RecallDate": "2025-06-10T00:00:00", "URL": "https://www.cpsc.gov/Recalls/2025/graco",
        "Hazards": [{"Name": "Fall hazard"}], "Remedies": [{"Name": "Refund"}],
        "Products": [{"Name": "Graco crib"}], "Manufacturers": [{"Name": "Graco Children's Products"}],
    },
    {
        "RecallID": 2, "RecallNumber": "24002", "Title": "Other Brand Cribs Recalled",
        "RecallDate": "2024-01-05T00:00:00", "URL": "https://www.cpsc.gov/Recalls/2024/other",
        "Hazards": [], "Remedies": [], "Products": [{"Name": "Crib"}], "Manufacturers": [{"Name": "CribCo"}],
    },
]


class FakeResponse:
    def __init__(self, data, status=200):
        self._data, self.status_code = data, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=None)

    def json(self):
        return self._data


# Fake CPSC: returns crib recalls only when searching "crib"
def fake_get(url, params=None, timeout=None):
    if params and params.get("ProductName") == "crib":
        return FakeResponse(FAKE_CPSC)
    return FakeResponse([])


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setattr(products, "save_products", lambda: None)
    monkeypatch.setattr(recalls.httpx, "get", fake_get)
    recalls.recall_cache.clear()
    products.products_db[:] = [
        products.Product(id=1, name="Crib", brand="Graco", category="Baby", model_number="G1"),
        products.Product(id=2, name="Toaster", brand="Prestige", category="Kitchen", model_number="T1"),
        products.Product(id=3, name="Crib", brand="NoRecallBrand", category="Baby", model_number="N1"),
    ]


def test_product_with_matching_recall():
    r = client.get("/products/1/recalls")
    assert r.status_code == 200
    body = r.json()
    assert body["recalled"] is True
    assert body["total_matches"] == 1          # only the Graco recall, not CribCo
    assert body["recalls"][0]["recall_number"] == "25001"


def test_same_name_other_brand_is_not_matched():
    body = client.get("/products/3/recalls").json()
    assert body["recalled"] is False
    assert body["recalls"] == []


def test_product_with_no_recalls():
    body = client.get("/products/2/recalls").json()
    assert body["recalled"] is False


def test_unknown_product_returns_404_json():
    r = client.get("/products/99/recalls")
    assert r.status_code == 404
    assert r.json() == {"detail": "Product not found"}


def test_alerts_lists_only_recalled_products():
    body = client.get("/alerts").json()
    assert body["products_checked"] == 3
    assert body["products_recalled"] == 1
    assert body["alerts"][0]["product"]["id"] == 1


def test_cpsc_down_returns_502_json(monkeypatch):
    monkeypatch.setattr(recalls.httpx, "get", lambda *a, **k: FakeResponse([], status=500))
    r = client.get("/alerts")
    assert r.status_code == 502
    assert "detail" in r.json()
