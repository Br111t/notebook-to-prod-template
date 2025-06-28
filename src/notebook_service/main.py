# app/main.py
from pathlib import Path

from fastapi import FastAPI, HTTPException

from notebook_service.runner import run_notebook
from notebook_service.schemas import NotebookOutputs  # ← import your schema

app = FastAPI(
    title="Notebook-to-API",
    debug=True,
    description=(
        "Execute Jupyter notebooks via REST and "
        "analyze text via IBM Watson NLU."
    ),
    version="0.1.0",
)


@app.get(
    "/run/{notebook_name}",
    response_model=NotebookOutputs,  # ← tell FastAPI what you return
    tags=["execution"],
    summary="Execute a notebook and fetch its last‐cell outputs",
)
async def run_notebook_endpoint(notebook_name: str):
    """
    Execute the given notebook (by name) and return its last‐cell outputs.
    """
    path = Path("notebooks") / f"{notebook_name}.ipynb"
    if not path.exists():
        raise HTTPException(
            status_code=404, detail=f"Notebook `{notebook_name}` not found"
        )

    return run_notebook(str(path))
