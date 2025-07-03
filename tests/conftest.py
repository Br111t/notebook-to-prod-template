# tests/conftest.py
import asyncio

import nbformat
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True, scope="session")
def use_selector_event_loop():
    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="session")
def client():
    # import inside the fixture so coverage can start first
    from notebook_service.main import app
    return TestClient(app)


@pytest.fixture
def sample_notebook(tmp_path):
    """
    Create a minimal empty notebook file named <name>.ipynb in tmp_path.
    Returns the pathlib.Path to that file.
    """
    def _create(name="example"):
        nb = nbformat.v4.new_notebook()
        file = tmp_path / f"{name}.ipynb"
        file.write_text(nbformat.writes(nb))
        return file
    return _create
