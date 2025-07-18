# src/notebook_service/main.py
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from starlette.concurrency import run_in_threadpool

from notebook_service import __version__
from notebook_service.runner import DEFAULT_NOTEBOOK_DIR, run_notebook
from notebook_service.schemas import NotebookOutputs

app = FastAPI(
    title="Notebook Execution Service",
    description="Execute Jupyter notebooks and return their outputs.",
    version=__version__,
)


# necessary to execise the API layer
@app.get(
    "/run/{notebook_name}",
    response_model=NotebookOutputs,
    summary="Execute a notebook and fetch its outputs",
)
async def run_notebook_endpoint(notebook_name: str):

    notebooks_dir = Path(os.getenv("NOTEBOOK_DIR", DEFAULT_NOTEBOOK_DIR))

    nb_path = notebooks_dir / f"{notebook_name}.ipynb"
    if not nb_path.exists():
        raise HTTPException(status_code=404, detail="Notebook not found")

    # Pass the *absolute* path so run_notebook uses it verbatim
    return await run_in_threadpool(run_notebook, str(nb_path))
