"""
Health Endpoint Tests
"""


def test_health_endpoint(client):
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["api_name"] == "CancerInfo API"
    assert data["api_version"] == "1.0.0"
    assert data["source_registry_count"] > 0
    assert data["approved_cancers_count"] > 0


def test_root_health_endpoints(client):
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "ok"}

    res_api_health = client.get("/api/health")
    assert res_api_health.status_code == 200
    assert res_api_health.json() == {"status": "ok"}


def test_custom_compliance_headers(client):
    response = client.get("/v1/cancers")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert "X-Response-Time-MS" in response.headers
    assert response.headers.get("X-Medical-Disclaimer") == "Informational only; not medical advice"
    assert response.headers.get("X-Disclaimer") == "Informational API only. Not medical advice."
    assert response.headers.get("X-CancerInfo-API-Version") == "1.0.0"

