import sys
from pathlib import Path

import nbformat
import networkx as nx
import pandas as pd
from nbclient import execute


def run_notebook(path: str):
    """
    Execute a Jupyter notebook and return its cell outputs.

    Args:
        path: Path to the notebook file.
    Returns:
        A dict with a single key 'outputs' containing a
        list of output strings from all notebook cells.
    """
    # Determine project root (runner.py is in
    # PROJECT_ROOT/src/notebook_service)
    project_root = Path(__file__).resolve().parents[2]

    # Make sure notebooks can import our package:
    src_dir = project_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    # Resolve the notebook path to an absolute path
    nb_file = Path(path).resolve()

    # Read the notebook
    with nb_file.open("r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    # Execute the notebook with working directory
    # set to the notebooks directory
    notebooks_dir = project_root / "notebooks"
    executed_nb = execute(nb, cwd=str(notebooks_dir), kernel_name="python3")

    # Collect outputs from all cells
    outputs = []
    for cell in executed_nb.cells:
        for out in cell.get("outputs", []):
            ot = out.get("output_type")
            if ot == "stream":
                outputs.append(out.get("text", ""))
            elif "data" in out:
                # Use text/plain representation if available
                text = out.get("data", {}).get("text/plain")
                if text is not None:
                    outputs.append(text)

    return {"outputs": outputs}


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
