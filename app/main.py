from fastapi import FastAPI, HTTPException
from nbclient import NotebookClient
from .runner import run_notebook
import nbformat
import pathlib


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



app = FastAPI()

@app.get("/run/{notebook_name}")
async def run_notebook_endpoint(notebook_name: str):
    path = pathlib.Path("notebooks") / f"{notebook_name}.ipynb"
    if not path.exists():
        raise HTTPException(404, "Notebook not found")
    result = run_notebook(str(path))
    return {"notebook": notebook_name, "result": result}

