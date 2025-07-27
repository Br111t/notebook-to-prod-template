# tests/conftest.py
import asyncio
import importlib
import os
from pathlib import Path
from types import SimpleNamespace

import nbformat
import pytest
from fastapi.testclient import TestClient

import notebook_service.main as main_mod
import notebook_service.runner as runner_mod


@pytest.fixture(autouse=True, scope="session")
def use_selector_event_loop():
    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(autouse=True)
def env_setup(monkeypatch, tmp_path):
    # Set SERVICE_APIKEY for auth
    monkeypatch.setenv("SERVICE_APIKEY", "secret")
    # Redirect NOTEBOOK_DIR to tmp_path
    monkeypatch.setenv("NOTEBOOK_DIR", str(tmp_path))
    # Override module-level constants so both runner and main use tmp_path
    monkeypatch.setattr(main_mod, "NOTEBOOK_DIR", tmp_path, raising=False)
    monkeypatch.setattr(runner_mod, "NOTEBOOK_DIR", tmp_path, raising=False)


@pytest.fixture
def auth_header():
    """Returns the header dict for service key auth."""
    return {"X-SERVICE-Key": "secret"}


@pytest.fixture
def sample_notebook():
    """
    Factory to create a minimal .ipynb in NOTEBOOK_DIR and rebuild
    the NotebookName enum.
    Usage:
        sample_notebook(name="sfe")
    """
    def _create(name: str):
        nb = nbformat.v4.new_notebook()
        file_path = Path(os.getenv("NOTEBOOK_DIR")) / f"{name}.ipynb"
        file_path.write_text(nbformat.writes(nb))

        # rebuild the enum _after_ the file exists
        main_mod.NotebookName = main_mod._make_notebook_enum()

        # return the Path
        return file_path

    # return the factory
    return _create


@pytest.fixture
def client():
    """
    Create a TestClient after rebuilding the NotebookName enum
    to match current files.
    """
    # Ensure enum is up-to-date before instantiating the client
    main_mod.NotebookName = main_mod._make_notebook_enum()
    importlib.reload(main_mod)
    return TestClient(main_mod.app)


@pytest.fixture(autouse=True)
def set_api_keys_env():
    os.environ.setdefault("NLU_URL", "https://example.com")
    os.environ.setdefault("NLU_APIKEY", "test_dummy_key")
    os.environ.setdefault("SERVICE_APIKEY", "secret")


@pytest.fixture(autouse=True)
def point_to_tmp(sample_notebook, tmp_path, monkeypatch):
    monkeypatch.setattr(runner_mod, "NOTEBOOK_DIR", tmp_path)
    monkeypatch.setenv("NOTEBOOK_DIR", str(tmp_path))


@pytest.fixture
def dummy_nb():
    # Only needs a .cells attribute
    return SimpleNamespace(cells=[{
        "outputs": [
            {"output_type": "stream",       "text": "seq1"},
            {"output_type": "display_data", "data": {"text/plain": "seq2"}},
            {"output_type": "display_data", "data": {}},
        ]
    }])


@pytest.fixture(autouse=True)
def patch_notebook_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("NOTEBOOK_DIR", str(tmp_path))
    monkeypatch.setattr(runner_mod, "NOTEBOOK_DIR", tmp_path, raising=False)
