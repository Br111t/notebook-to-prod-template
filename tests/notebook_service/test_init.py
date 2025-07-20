# tests/notebook_service/test_init.py
import importlib
from importlib.metadata import PackageNotFoundError

# NOTE: the package name here must match the one you pass to version()
DIST_NAME = "notebook-to-prod-template"


def test_version_from_metadata(monkeypatch):
    # Stub version() to return something realistic
    monkeypatch.setattr(
        "importlib.metadata.version",
        lambda name: "1.2.3" if name == DIST_NAME else "bad"
    )
    # reload the package so __version__ is re‑computed
    import notebook_service
    importlib.reload(notebook_service)
    assert notebook_service.__version__ == "1.2.3"


def test_version_fallback(monkeypatch):
    # version() to raise PackageNotFoundError
    def fake_version(name):
        raise PackageNotFoundError
    monkeypatch.setattr("importlib.metadata.version", fake_version)

    # reload to trigger the except branch
    import notebook_service
    importlib.reload(notebook_service)
    assert notebook_service.__version__ == "0.0.0.dev0"
