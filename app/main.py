from fastapi import FastAPI
from nbclient import NotebookClient
import nbformat

# This is a simple FastAPI application that runs a Jupyter notebook
# when a POST request is made to the /run-notebook endpoint.
# The notebook's output is returned as a response.
# It is intended to be used as a template for deploying Jupyter notebooks
# in production environments.
# It can be run with `uvicorn app.main:app --reload` command.
# The notebook to be executed is specified in the code below.
# Make sure to have the notebook file (example.ipynb) in the same directory as this script.

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Notebook-to-Prod Template is up!"}

@app.post("/run-notebook")
def run_notebook():
    # loads and executes the notebook, returns its cells' output
    nb = nbformat.read("example.ipynb", as_version=4)

    client = NotebookClient(nb, kernel_name="python3")
    # You can specify the kernel name if needed, e.g., "python3"
    # If you have a specific kernel to use, make sure it is installed in your environment
    client.execute()
    return {"executed_cells": len(nb.cells)}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)