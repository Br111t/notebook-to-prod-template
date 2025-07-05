# src/notebook_service/runner.py
import os
import re
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


def preprocess_concepts(df: pd.DataFrame,
                        relevance_threshold: float = 0.49) -> pd.DataFrame:
    """
    Clean and filter NLU-extracted concepts.
    Assumes df has 'concepts_raw' column (List[Dict]).
    Adds 'concepts_filtered' (List[str]) per row.
    """

    # re-flatten including typeHierarchy and
    # apply your relevance threshold
    records = []
    for idx, row in df.iterrows():
        for c in row["concepts_raw"]:
            if c.get("relevance", 0) >= relevance_threshold:
                records.append({
                    "doc_index":     idx,
                    "concept":       c["text"],
                    "relevance":     c["relevance"],
                })

    dfc = pd.DataFrame(records)

    # deduplicate on concept, keeping the highest‐relevance entry
    df_unique = (
        dfc
        .sort_values("relevance", ascending=False)
        .reset_index(drop=True)
    )

    # Drop high-relevance outliers driven by NLU co-mentions,
    # not by semantic importance
    junk = re.compile(r"\b(?:album|song|people|hat|TeX|Tent)\b",
                      flags=re.IGNORECASE)
    df_clean = df_unique[~df_unique["concept"].str.contains(junk)]
    df_concepts_final = df_clean.drop(
        df_clean.index[34:56]).reset_index(drop=True)

    return df_concepts_final


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
