from nbclient import NotebookClient
from nbformat import read

def run_notebook(path: str, parameters: dict = None) -> dict:
    nb = read(path, as_version=4)
    if parameters:
        # inject parameters cell or use papermill style
        pass
    client = NotebookClient(nb)
    client.execute()
    # extract outputs (e.g., the last cell’s data or visuals)
    # result = { … }
    return result


