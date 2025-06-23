from fastapi import FastAPI
from nbclient import NotebookClient
import nbformat


app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Notebook-to-Prod Template is up!"}


@app.post("/run-notebook")
def run_notebook():
    # loads and executes the notebook, returns its cells' output
    nb = nbformat.read(
        "example.ipynb",
        as_version=4,
    )
    client = NotebookClient(
        nb,
        kernel_name="python3",
    )
    client.execute()
    return {"executed_cells": len(nb.cells)}