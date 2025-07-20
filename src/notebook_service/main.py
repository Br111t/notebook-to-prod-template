# src/notebook_service/main.py
import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

import nbformat
from fastapi import FastAPI, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from nbclient import NotebookClient
from starlette.concurrency import run_in_threadpool

from notebook_service import __version__
from notebook_service.runner import DEFAULT_NOTEBOOK_DIR, run_notebook
from notebook_service.schemas import NotebookOutputs

if sys.platform.startswith("win"):
    # only set the Windows selector policy on Windows hosts
    from asyncio import WindowsSelectorEventLoopPolicy
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())


app = FastAPI(
    title="Notebook Execution Service",
    description="Execute Jupyter notebooks and return their outputs.",
    version=__version__,
)
start_time = time.time()


@app.get("/health")
async def health():
    # 1) Basic server liveness
    result = {"status": "ok"}

    # 2) Uptime
    result["uptime_seconds"] = int(time.time() - start_time)

    # 3) Version from __init__.py
    from notebook_service import __version__
    result["version"] = __version__

    # 4) Optional: ping NLU in DEV_MODE only, not to slow prod
    if os.getenv("DEV_MODE", "false") == "false":
        try:
            from notebook_service.emotion import NLU_CLIENT

            # a no-op or minimal call, adjust as needed
            _ = NLU_CLIENT   # maybe call .analyze with dummy text
            result["nlu"] = "reachable"
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"NLU error: {e}")

    return result


def get_api_key(x_api_key: str = Security(APIKeyHeader(name="X-API-Key"))):
    expected = os.getenv("NLU_APIKEY")
    if expected is None:
        raise HTTPException(500, "Server misconfiguration: NLU_APIKEY not set")
    if x_api_key != expected:
        raise HTTPException(403, "Invalid API key")
    return x_api_key


@app.get("/run")
async def run_notebook_query(
    notebook: str,
    fmt: str = "trimmed",
    api_key: str = Security(get_api_key)
):
    # Resolve the file on disk
    notebooks_dir = Path(os.getenv("NOTEBOOK_DIR", DEFAULT_NOTEBOOK_DIR))
    nb_path = notebooks_dir / notebook
    if not nb_path.exists():
        raise HTTPException(status_code=404, detail="Notebook not found")

    # Execute the notebook (raw JSON)
    outputs = await run_in_threadpool(run_notebook, str(nb_path))

    if fmt.lower() == "raw":
        return outputs  # full JSON
    # otherwise return the trimmed version
    else:
        return filter_notebook(outputs)  # your pruned version


def filter_notebook(nb_json: dict) -> dict:
    """
    Prune a full notebook JSON to only keep stream and plan-text results.
    """
    for cell in nb_json.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        new_outputs = []
        for o in cell.get("outputs", []):
            if o.get("output_type") == "stream":
                new_outputs.append(o)
            elif o.get("output_type") == "execute_result":
                text = o.get("data", {}).get("text/plain")
                if text is not None:
                    new_outputs.append({
                        "output_type": "execute_result",
                        "data": {"text/plain": text},
                        "execution_count": o.get("execution_count")
                    })
        cell["outputs"] = new_outputs
    return nb_json


# necessary to exercise the API layer
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


def list_cells(path):
    nb = nbformat.read(path, as_version=4)
    for idx, cell in enumerate(nb.cells):
        preview = cell.source.strip().splitlines()[0] if cell.source else ""
        print(f"{idx:3d}: {cell.cell_type:<5} {preview!r}")


def run_and_filter(path, to_run):
    from pathlib import Path

    # read & slice…
    notebook_dir = Path(path).parent
    nb_full = nbformat.read(path, as_version=4)
    nb = nbformat.v4.new_notebook(metadata=nb_full.metadata)
    nb.cells = [nb_full.cells[i] for i in to_run]
    client = NotebookClient(nb, timeout=600, kernel_name="python3")
    # switch into the notebook's directory so relative paths line up
    orig_cwd = os.getcwd()
    os.chdir(notebook_dir)
    try:
        client.execute()
    finally:
        os.chdir(orig_cwd)

    # prune outputs…
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue

        new_out = []
        for o in cell.get("outputs", []):
            # keep STDOUT / STDERR streams untouched
            if o.output_type == "stream":
                new_out.append(o)

            # for execute_reults , drop HTML and metadata, only keep
            # plain text
            elif o.output_type == "execute_result":
                text = o.data.get("text/plain")
                if text is not None:
                    new_out.append({
                        "output_type": "execute_result",
                        "data": {"text/plain": text},
                        "execution_count": o.execution_count
                    })
        cell.outputs = new_out

    # Signal completion
    print(f"✅ Completed run_and_filter on {Path(path).name}. "
          f"Check data/processed for the CSV & JSON outputs.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="notebook_service",
        description="List cells or execute & filter a notebook"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list-cells subcommand
    lc = subparsers.add_parser(
        "list-cells",
        help="Print all cell indices (and first-line previews) for a notebook"
    )
    lc.add_argument(
        "-n", "--notebook",
        required=True,
        help="Path to the notebook (.ipynb) to inspect"
    )

    # run subcommand
    run_cmd = subparsers.add_parser(
        "run",
        help="Execute a subset of cells and print the filtered JSON"
    )
    run_cmd.add_argument(
        "-n", "--notebook",
        required=True,
        help="Path to the notebook (.ipynb) to execute"
    )

    # choose the cells in the notebook to run
    run_cmd.add_argument(
        "--cells",
        nargs="+",
        type=int,
        required=True,
        help="Cell indices to run eg. --cells 1 2 3"
    )

    args = parser.parse_args()

    if args.command == "list-cells":
        list_cells(args.notebook)
    elif args.command == "run":
        # --cells is now required, so we can use it directly
        run_and_filter(args.notebook, args.cells)
