# tests/test_main.py

import importlib
import sys
from pathlib import Path

import nbformat
import pytest
from fastapi.testclient import TestClient

from notebook_service import main as app_main
from notebook_service.main import (
    app,
    filter_notebook,
    list_cells,
    run_and_filter,
)

client = TestClient(app)

#
# 1) Integration tests for /run/{notebook_name}
#


@pytest.mark.parametrize(
    "notebook_stem, notebook_query, status_code",
    [
        ("sfe", "sfe.ipynb", 200),      # exists
        ("example", "example.ipynb", 422),
    ],
)
def test_run_endpoint(
    sample_notebook,
    auth_header,
    notebook_stem,
    notebook_query,
    status_code
):
    # create the notebook file
    if notebook_stem == "sfe":
        sample_notebook(name=notebook_stem)

    # relaod the app so that _make_notebook_enum runs with new notebook
    importlib.reload(app_main)

    # spin up TestClient againts that reloaded app
    client = TestClient(app_main.app)

    # hit the endpoint with the required API key
    response = client.get(
        "/run",
        params={"notebook": notebook_query},
        headers=auth_header,
    )

    print("STATUS:", response.status_code)
    print("BODY:  ", response.json())

    assert response.status_code == status_code


# def test_run_notebook_executes_cells(tmp_path):
#     nb = nbformat.v4.new_notebook()
#     nb.cells.append(nbformat.v4.new_code_cell("print('hello world')"))
#     path = tmp_path / "foo.ipynb"
#     path.write_text(nbformat.writes(nb))

#     result = run_notebook(str(path))
#     outputs = result.get("outputs", [])
#     assert outputs, "No outputs found"

#     stream_data = [o["data"] for o in outputs if o.get("type") == "stream"]
#     assert any("hello world" in d for d in stream_data)


#
# 2) /health endpoint
#

def test_health_ok(monkeypatch):
    monkeypatch.setenv("DEV_MODE", "false")
    # Ensure NLU_CLIENT importable

    class Dummy:
        pass
    monkeypatch.setattr(
        "notebook_service.emotion.NLU_CLIENT",
        Dummy,
        raising=False
    )

    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert isinstance(body["uptime_seconds"], int)
    from notebook_service import __version__
    assert body["version"] == __version__


def test_health_nlu_unreachable(monkeypatch):
    monkeypatch.setenv("DEV_MODE", "false")
    # Force an error when accessing NLU_CLIENT
    monkeypatch.setitem(sys.modules, "notebook_service.emotion", {})
    monkeypatch.setattr(
        "notebook_service.emotion.NLU_CLIENT",
        property(lambda _: (_ for _ in ()).throw(RuntimeError("down"))),
        raising=False,
    )

    resp = client.get("/health")
    assert resp.status_code == 503
    assert "NLU error" in resp.json()["detail"]


#
# 3) /run?notebook=...&fmt=trimmed query endpoint
#


def write_notebook_file(path: Path):
    nb = nbformat.v4.new_notebook()
    nb.cells.append(nbformat.v4.new_code_cell("print('xyz')"))
    path.write_text(nbformat.writes(nb))


def test_run_query_not_found(client, auth_header):
    resp = client.get(
        "/run?notebook=does_not_exist&fmt=trimmed",
        headers=auth_header,
    )
    assert resp.status_code == 422


# missing header → 401 Unauthorized
def test_run_query_missing_key(client):
    resp = client.get(
        "/run",
        params={"notebook": "foo.ipynb", "fmt": "trimmed"},
    )
    assert resp.status_code == 401


# wrong header → 403 Forbidden
def test_run_query_wrong_key(client):
    resp = client.get(
        "/run",
        params={"notebook": "foo.ipynb", "fmt": "trimmed"},
        headers={"X-SERVICE-Key": "not-the-right-one"},
    )
    assert resp.status_code == 403


# happy‐path: write foo.ipynb, then get trimmed outputs
def test_run_query_success_trimmed(
        sample_notebook,
        client,
        auth_header):
    # write foo.ipynb under tmp_path and rebuild Enum
    sample_notebook(name="foo")

    # relaod the app so that _make_notebook_enum runs with new notebook
    importlib.reload(app_main)

    # spin up TestClient againts that reloaded app
    client = TestClient(app_main.app)

    response = client.get(
        "/run",
        params={"notebook": "foo.ipynb", "fmt": "trimmed"},
        headers=auth_header,
    )

    assert response.status_code == 200

    data = response.json()
    assert "outputs" in data
    assert isinstance(data["outputs"], list)


##
# 4) filter_notebook unit test
#


@pytest.fixture
def raw_nb():
    return {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {"output_type": "stream", "data": "hello"},
                    {
                        "output_type": "execute_result",
                        "data": {"text/plain": "42"},
                        "execution_count": 1,
                    },
                    {"output_type": "display_data",
                     "data": {"text/html": "<b>nope</b>"}
                     },
                ],
            },
            {"cell_type": "markdown", "source": "## ignore me"},
        ]
    }


def test_filter_only_keeps_stream_and_plain_execute(raw_nb):
    pruned = filter_notebook(raw_nb.copy())
    outs = pruned["cells"][0]["outputs"]
    assert len(outs) == 2
    assert all(o["output_type"] in {"stream", "execute_result"} for o in outs)


#
# 5) CLI helpers
#


def test_list_cells_prints_indices(tmp_path, capsys):
    nb = nbformat.v4.new_notebook()
    nb.cells.append(nbformat.v4.new_code_cell("print('a')"))
    nb.cells.append(nbformat.v4.new_markdown_cell("hi"))
    path = tmp_path / "test.ipynb"
    path.write_text(nbformat.writes(nb))

    list_cells(str(path))
    out = capsys.readouterr().out
    # should mention index and cell type and preview
    assert "0: code" in out
    assert "print('a')" in out
    assert "1: markdown" in out
    assert "hi" in out


def test_run_and_filter_executes_and_filters(tmp_path, capsys, monkeypatch):
    nb = nbformat.v4.new_notebook()
    nb.cells.append(nbformat.v4.new_code_cell("print('ok')"))
    nb.cells.append(nbformat.v4.new_code_cell("1+1"))
    path = tmp_path / "foo.ipynb"
    path.write_text(nbformat.writes(nb))

    class DummyClient:
        def __init__(self, nb, timeout, kernel_name): pass
        def execute(self): pass

    monkeypatch.setattr("notebook_service.main.NotebookClient", DummyClient)

    run_and_filter(str(path), [0, 1])
    out = capsys.readouterr().out
    assert "✅ Completed run_and_filter on foo.ipynb" in out
