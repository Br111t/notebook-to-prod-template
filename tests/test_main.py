# tests/test_main.py
# ensures your API layer works.
import os
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_run_endpoint_success():
    response = client.get("/run/example")
    assert response.status_code == 200
    data = response.json()
    assert "outputs" in data
    assert any("4" in out for out in data["outputs"])

def test_run_endpoint_not_found():
    resp = client.get("/run/does_not_exist")
    assert resp.status_code == 404
