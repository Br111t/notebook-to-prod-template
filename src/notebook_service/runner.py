# src/notebook_service/runner.py
import os
from pathlib import Path

import nbformat
import nest_asyncio
import networkx as nx
import pandas as pd
from nbclient import execute

DEFAULT_NOTEBOOK_DIR = Path(__file__).resolve().parent / "notebooks"
NOTEBOOK_DIR = Path(os.getenv("NOTEBOOK_DIR", DEFAULT_NOTEBOOK_DIR))


nest_asyncio.apply()


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
    executed_nb = execute(
        nb,
        kernel_name="python3",
        cwd=str(nb_path.parent),  # run from the notebook’s folder
    )

    # Structured objects with type and data
    collected: list[dict] = []
    for idx, cell in enumerate(executed_nb.cells, start=1):
        for out in cell.get("outputs", []):
            ot = out["output_type"]
            if ot == "stream":
                collected.append(
                    {"cell": idx,
                     "type": ot,
                     "data": out["text"]})
            else:
                txt = out["data"].get("text/plain")
                if txt:
                    collected.append(
                        {"cell": idx,
                         "type": ot,
                         "data": txt})

    return {"outputs": collected}


def load_data(path: str) -> pd.DataFrame:
    """
    Stub for loading a CSV or other tabular data into a DataFrame.
    """
    return pd.read_csv(path)


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stub for any DataFrame cleaning / feature extraction.
    """
    # e.g. df["clean_text"] = df["text"].str.lower()
    return df


def build_semantic_graph(df: pd.DataFrame) -> nx.Graph:
    """
    Stubbed implementation — replace with your real graph‐building logic.
    """
    G = nx.Graph()
    # e.g. for each concept in df.concepts:
    #     G.add_node(concept)
    return G


def compute_centrality(G: nx.Graph) -> dict:
    return nx.degree_centrality(G)
