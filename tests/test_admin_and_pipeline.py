"""
Admin and Pipeline Tests
"""
from app.core.config import settings


def test_admin_unauthorized(client):
    response = client.post("/v1/admin/ingest", json={"source_id": "nci-us"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_admin_authorized_seed(client):
    headers = {"X-Admin-Key": settings.ADMIN_API_KEY}
    response = client.post("/v1/admin/seed", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["message"] == "Seed routine executed successfully."


def test_categories_endpoint(client):
    response = client.get("/v1/categories")
    assert response.status_code == 200
    cats = response.json()["data"]
    assert len(cats) >= 30
    slugs = [c["category"] for c in cats]
    assert "symptoms" in slugs
    assert "screening" in slugs
    assert "biomarkers" in slugs
    assert "staging" in slugs


def test_countries_endpoint(client):
    response = client.get("/v1/countries")
    assert response.status_code == 200
    countries = response.json()["data"]
    codes = [c["code"] for c in countries]
    assert "US" in codes
    assert "GB" in codes
    assert "AU" in codes
    assert "GLOBAL" in codes
