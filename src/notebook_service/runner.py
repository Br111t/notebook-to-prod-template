# src/notebook_service/runner.py
import os
from pathlib import Path

import nbformat
import nest_asyncio
import pandas as pd
from nbclient import execute

DEFAULT_NOTEBOOK_DIR = Path(__file__).resolve().parent / "notebooks"
NOTEBOOK_DIR = Path(os.getenv("NOTEBOOK_DIR", DEFAULT_NOTEBOOK_DIR))


nest_asyncio.apply()


def load_data(path: str) -> pd.DataFrame:
    """
    Stub for loading a CSV or other tabular data into a DataFrame.
    """
    return pd.read_csv(path)


def run_notebook(path: str):
    """
    Execute a Jupyter notebook and return a dict of its cell outputs.

    - If *path* is relative, it's resolved inside NOTEBOOK_DIR.
    - The “.ipynb” suffix is added automatically if missing.
    """
    # Resolve the notebook file path
    nb_path = Path(path)
    if nb_path.suffix != ".ipynb":
        nb_path = nb_path.with_suffix(".ipynb")

    if not nb_path.is_absolute():
        nb_path = NOTEBOOK_DIR / nb_path

    nb_path = nb_path.resolve(strict=True)  # raises FileNotFoundError

    # Load & execute
    nb = nbformat.read(nb_path, as_version=4)
    exec_kwargs = {
        "kernel_name": "python3",
        "cwd": str(nb_path.parent),
    }
    executed_nb = execute(
        nb,
        **exec_kwargs
    )

    # Structured objects with type and data
    collected: list[dict] = []
    allowed_mimes = {
        "text/plain",
        "application/json",
        "text/csv",
        "image/png",
    }

    for idx, cell in enumerate(executed_nb.cells, start=1):
        for out in cell.get("outputs", []):
            ot = out.get("output_type")

            if ot == "stream":
                collected.append({
                    "cell": idx,
                    "type": ot,
                    "mime": "text/plain",
                    "data": out.get("text", "")
                })
                continue

            if ot in ("execute_result", "display_data"):
                data_dict = out.get("data") or {}
                for mime_type, content in data_dict.items():
                    if mime_type not in allowed_mimes:
                        continue
                    collected.append({
                        "cell": idx,
                        "type": ot,
                        "mime": mime_type,
                        "data": content
                    })

    return {"outputs": collected}
