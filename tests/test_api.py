from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SyncLM Studio"


def test_api_metadata():
    res = client.get("/api/metadata")
    assert res.status_code == 200
    data = res.json()
    assert len(data["technologies"]) == 5
    assert len(data["vendors"]) == 6
    assert len(data["doc_types"]) == 4


def test_api_sources():
    res = client.get("/api/sources?technology=sase")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    assert all(s["technology"] == "sase" for s in data)


def test_api_targets():
    res = client.get("/api/targets")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1


def test_api_budget():
    res = client.post("/api/budget", json={
        "technologies": ["sase", "browser"],
        "vendors": ["panw", "zscaler"],
        "doc_types": ["architecture"]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["source_count"] > 0
    assert data["total_words"] > 0
    assert data["slot_usage_consolidated"] <= 50


def test_spa_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "<title>SyncLM Studio" in res.text
