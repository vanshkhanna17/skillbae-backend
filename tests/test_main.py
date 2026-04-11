from fastapi.testclient import TestClient


def test_ping(test_client: TestClient):
    response = test_client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"success": True}
