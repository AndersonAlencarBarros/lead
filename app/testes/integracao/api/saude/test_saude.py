from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_endpoint_reports_database_up(database_url):
    with client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}
