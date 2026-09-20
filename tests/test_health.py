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
