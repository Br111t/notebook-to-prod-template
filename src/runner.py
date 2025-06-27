# src/runner.py

import sys
from pathlib import Path
import nbformat
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
    # Resolve the notebook path to an absolute path
    nb_file = Path(path).resolve()

    # Determine project root (assuming this file is in PROJECT_ROOT/src)
    project_root = Path(__file__).resolve().parent.parent

    # Prepend paths to allow notebook imports
    sys.path.insert(0, str(project_root / "src"))
    sys.path.insert(0, str(project_root))

    # Read the notebook
    with open(nb_file, encoding="utf-8") as f:
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
