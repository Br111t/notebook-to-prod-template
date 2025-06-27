# tests/test_runner.py
# validates your notebook‐execution logic.
import os
from src.runner import run_notebook

HERE = os.path.dirname(__file__)


def test_example_notebook_runs(tmp_path):
    nb_src = os.path.join(HERE, "..", "notebooks", "example.ipynb")
    # Copy to temp path so runner.open() works
    nb_copy = tmp_path / "example.ipynb"
    nb_copy.write_bytes(open(nb_src, "rb").read())

    result = run_notebook(str(nb_copy))
    # We know example.ipynb prints "4\n" in its last cell:
    assert any("4" in out for out in result["outputs"])
