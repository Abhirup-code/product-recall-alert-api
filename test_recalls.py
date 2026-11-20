# testing
# These fake the CPSC API demo test not for prod

import httpx
import pytest
from fastapi.testclient import TestClient

import recalls
from main import app

client = TestClient(app)

FAKE_CPSC = [
    {
        "RecallID": 1, "RecallNumber": "24001", "Title": "Old Crib Recall",
        "RecallDate": "2023-01-05T00:00:00", "URL": "https://www.cpsc.gov/Recalls/2023/old",
        "Hazards": [{"Name": "Fall hazard"}], "Remedies": [{"Name": "Refund"}],
        "Products": [{"Name": "Baby crib"}], "Manufacturers": [{"Name": "CribCo"}],
    },
    {
        "RecallID": 2, "RecallNumber": "25002", "Title": "New Crib Recall",
        "RecallDate": "2025-06-10T00:00:00", "URL": "https://www.cpsc.gov/Recalls/2025/new",
        "Hazards": [], "Remedies": [], "Products": [], "Manufacturers": [],
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


@pytest.fixture(autouse=True)
def clear_cache():
    recalls.recall_cache.clear()


def test_search_returns_mapped_recalls(monkeypatch):
    monkeypatch.setattr(recalls.httpx, "get", lambda *a, **k: FakeResponse(FAKE_CPSC))
    r = client.get("/recalls", params={"query": "crib"})
    assert r.status_code == 200
    body = r.json()
    assert body["total_found"] == 2
    first = body["recalls"][0]
    assert first["title"] == "New Crib Recall"          # newest first
    assert body["recalls"][1]["hazard"] == "Fall hazard"
    assert body["recalls"][1]["date"] == "2023-01-05"


def test_limit(monkeypatch):
    monkeypatch.setattr(recalls.httpx, "get", lambda *a, **k: FakeResponse(FAKE_CPSC))
    r = client.get("/recalls", params={"query": "crib", "limit": 1})
    body = r.json()
    assert body["returned"] == 1
    assert body["links"][-1]["rel"] == "next"


def test_offset(monkeypatch):
    monkeypatch.setattr(recalls.httpx, "get", lambda *a, **k: FakeResponse(FAKE_CPSC))
    body = client.get("/recalls", params={"query": "crib", "offset": 1}).json()
    assert body["recalls"][0]["title"] == "Old Crib Recall"


def test_cache_calls_cpsc_once(monkeypatch):
    calls = []
    def fake_get(*a, **k):
        calls.append(1)
        return FakeResponse(FAKE_CPSC)
    monkeypatch.setattr(recalls.httpx, "get", fake_get)
    client.get("/recalls", params={"query": "crib"})
    client.get("/recalls", params={"query": "CRIB"})
    assert len(calls) == 1


def test_short_query_rejected():
    assert client.get("/recalls", params={"query": "a"}).status_code == 400


def test_cpsc_timeout_returns_504(monkeypatch):
    def boom(*a, **k):
        raise httpx.ReadTimeout("slow")
    monkeypatch.setattr(recalls.httpx, "get", boom)
    r = client.get("/recalls", params={"query": "crib"})
    assert r.status_code == 504
    assert "timed out" in r.json()["detail"]


def test_cpsc_down_returns_502(monkeypatch):
    monkeypatch.setattr(recalls.httpx, "get", lambda *a, **k: FakeResponse([], status=500))
    assert client.get("/recalls", params={"query": "crib"}).status_code == 502
