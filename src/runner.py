# src/runner.py
import nbformat
from nbclient import NotebookClient


def run_notebook(path: str):
    # read with v4 format
    nb = nbformat.read(path, 4)

    # execute all cells
    client = NotebookClient(nb, timeout=600)
    client.execute()

    return nb
