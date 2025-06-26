# app/runner.py
import pathlib
from nbclient import NotebookClient
from nbformat import read, NO_CONVERT

def run_notebook(path: str) -> dict:
    """
    Execute the notebook at `path` and return a dict of outputs from its last cell.
    """
    nb_path = pathlib.Path(path)
    nb = read(nb_path.open(), as_version=4, NO_CONVERT)
    client = NotebookClient(nb, timeout=600, kernel_name="python3")
    client.execute()
    # Assume the last cell has an output we care about:
    last_cell = nb.cells[-1]
    outputs = []
    for out in last_cell.get("outputs", []):
        if out.output_type == "execute_result":
            outputs.append(out["data"].get("text/plain"))
        elif out.output_type == "stream":
            outputs.append(out["text"])
    return {"outputs": outputs}
