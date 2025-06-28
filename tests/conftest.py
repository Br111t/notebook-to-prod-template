# tests/conftest.py
import asyncio

import nbformat
import pytest
from fastapi.testclient import TestClient

from notebook_service.main import app


@pytest.fixture(autouse=True, scope="session")
def use_selector_event_loop():
    # On Windows, force the selector policy so ZMQ/Tornado is happy
    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture
def sample_notebook(tmp_path):
    def _create(name="example"):
        nb = nbformat.v4.new_notebook()
        (tmp_path / f"{name}.ipynb").write_text(nbformat.writes(nb))
        return tmp_path / f"{name}.ipynb"

    return _create
