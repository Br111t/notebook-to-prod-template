# tests/test_main_full.py

import sys
from pathlib import Path

import nbformat
import pytest
from fastapi.testclient import TestClient

from notebook_service.main import (
    app,
    filter_notebook,
    list_cells,
    run_and_filter,
)
from notebook_service.runner import run_notebook

client = TestClient(app)

#
# 1) Integration tests for /run/{notebook_name}
#


@pytest.mark.parametrize(
    "notebook_name, status_code",
    [
        ("example", 200),      # exists
        ("does_not_exist", 404),
    ],
)
def test_run_endpoint(
    client,
    tmp_path,
    sample_notebook,
    monkeypatch,
    notebook_name,
    status_code
):
    # Point the service at our temporary directory
    monkeypatch.setenv("NOTEBOOK_DIR", str(tmp_path))

    if notebook_name == "example":
        # Use the sample_notebook fixture to write example.ipynb
        sample_notebook(name="example")

    resp = client.get(f"/run/{notebook_name}")
    assert resp.status_code == status_code


def test_run_notebook_executes_cells(tmp_path):
    nb = nbformat.v4.new_notebook()
    nb.cells.append(nbformat.v4.new_code_cell("print('hello world')"))
    path = tmp_path / "foo.ipynb"
    path.write_text(nbformat.writes(nb))

    result = run_notebook(str(path))
    outputs = result.get("outputs", [])
    assert outputs, "No outputs found"

    stream_data = [o["data"] for o in outputs if o.get("type") == "stream"]
    assert any("hello world" in d for d in stream_data)


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
@pytest.fixture(autouse=True)
def set_apikey(tmp_path, monkeypatch):
    monkeypatch.setenv("NLU_APIKEY", "secret")
    monkeypatch.setenv("NOTEBOOK_DIR", str(tmp_path))
    return tmp_path


def write_notebook_file(path: Path):
    nb = nbformat.v4.new_notebook()
    nb.cells.append(nbformat.v4.new_code_cell("print('xyz')"))
    path.write_text(nbformat.writes(nb))


def test_run_query_unauthorized(set_apikey):
    resp = client.get("/run?notebook=foo&fmt=trimmed")
    assert resp.status_code == 403


def test_run_query_not_found(set_apikey):
    resp = client.get(
        "/run?notebook=does_not_exist&fmt=trimmed",
        headers={"X-API-Key": "secret"},
    )
    assert resp.status_code == 404


def test_run_query_success_trimmed(set_apikey):
    # write foo.ipynb into NOTEBOOK_DIR
    nbfile = set_apikey / "foo.ipynb"
    write_notebook_file(nbfile)

    # call trimmed endpoint: it returns a dict of outputs
    resp = client.get(
        "/run?notebook=foo.ipynb&fmt=trimmed",
        headers={"X-API-Key": "secret"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # trimmed /filtered run_notebook_query returns 'outputs'
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
