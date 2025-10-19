import importlib

from fastapi.testclient import TestClient

from notebook_service import main as app_main


def test_health_dev_mode_skips_nlu(monkeypatch):
    monkeypatch.setenv("DEV_MODE", "true")
    importlib.reload(app_main)
    client = TestClient(app_main.app)

    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "ok"
    assert body.get("nlu") == "skipped"


def test_run_query_header_alt_casing_accepts_x_service_key(sample_notebook):
    sample_notebook(name="foo")
    importlib.reload(app_main)
    client = TestClient(app_main.app)

    resp = client.get(
        "/run",
        params={"notebook": "foo.ipynb", "fmt": "trimmed"},
        headers={"X-Service-Key": "secret"},
    )
    assert resp.status_code == 200


def test_run_query_header_legacy_accepts_x_api_key(sample_notebook):
    sample_notebook(name="bar")
    importlib.reload(app_main)
    client = TestClient(app_main.app)

    resp = client.get(
        "/run",
        params={"notebook": "bar.ipynb", "fmt": "trimmed"},
        headers={"X-API-Key": "secret"},
    )
    assert resp.status_code == 200
