# src/notebook_service/main.py
import argparse
import asyncio
import os
import sys
import time
from enum import Enum
from mimetypes import guess_type
from pathlib import Path

import nbformat
from fastapi import FastAPI, HTTPException
from fastapi import Path as PathParam
from fastapi import Query, Security
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security.api_key import APIKeyHeader
from nbclient import NotebookClient
from starlette.concurrency import run_in_threadpool

from notebook_service import __version__
from notebook_service.runner import DEFAULT_NOTEBOOK_DIR, run_notebook
from notebook_service.schemas import NotebookOutputs

# Global settings
SERVICE_ENV_VAR = "SERVICE_APIKEY"
DEV = os.getenv("DEV_MODE", "false").lower() == "true"
service_key_header = APIKeyHeader(name="X-SERVICE-Key", auto_error=False)

# Windows asyncio polict
if sys.platform.startswith("win"):
    # only set the Windows selector policy on Windows hosts
    from asyncio import WindowsSelectorEventLoopPolicy
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

# Load environment variables if present
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)

# Directory where notebooks live
NOTEBOOK_DIR = Path(os.getenv("NOTEBOOK_DIR", DEFAULT_NOTEBOOK_DIR))


def _make_notebook_enum():
    # dynamically build a string-based Enum for OpenAPI
    paths = list(NOTEBOOK_DIR.glob("*.ipynb"))
    if not paths:
        # no notebooks on disk → placeholder enum entry
        return Enum("NotebookName", {"no_notebooks_found": ""}, type=str)
    members = {p.stem: p.name for p in paths}
    # use type=str so values are treated as string enums in OpenAPI
    return Enum("NotebookName", members, type=str)


NotebookName = _make_notebook_enum()

# point at the real data/processed under /app
ROOT_DIR = Path(__file__).resolve().parents[2]   # /app
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# FastAPI application
app = FastAPI(
    title="Notebook Execution Service",
    description="Execute Jupyter notebooks and return their outputs.",
    version=__version__,
)
start_time = time.time()


@app.get("/health")
async def health():
    result = {"status": "ok"}
    result["uptime_seconds"] = int(time.time() - start_time)
    from notebook_service import __version__
    result["version"] = __version__
    try:
        from notebook_service.emotion import NLU_CLIENT
        NLU_CLIENT
        result["nlu"] = "reachable"
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"NLU error: {e}"
        )
    return result


def get_service_key(
        x_service_key: str = Security(service_key_header)
):
    if not x_service_key:
        raise HTTPException(401, "Missing service API key")
    expected = os.getenv("SERVICE_APIKEY")
    if not expected:
        raise HTTPException(
            500,
            f"Server misconfiguration: {SERVICE_ENV_VAR} not set"
        )
    if x_service_key != expected:
        raise HTTPException(
            403,
            "Invalid service API key"
        )
    return x_service_key


@app.get(
    "/run",
    summary="Execute a notebook and fetch its outputs",
    dependencies=[Security(get_service_key)],
    response_model=NotebookOutputs,
)
async def run_notebook_query(
    notebook: NotebookName = Query(
        ...,
        description="Select which notebook to execute",
    ),
    fmt: str = Query(
        "trimmed",
        enum=["trimmed", "raw"],
        description="Response format: `trimmed` or full `raw` JSON"
    ),
):
    if DEV:
        return {"outputs": []}
    if notebook.value == "":
        raise HTTPException(404, "No notebooks available to run")
    nb_path = NOTEBOOK_DIR / notebook.value
    if not nb_path.exists():
        raise HTTPException(status_code=404, detail="Notebook not found")
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
    allowed_mimes = {
        "text/plain",
        "application/json",
        "text/csv",
        "image/png",
    }

    for cell in nb_json.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        new_outputs: list[dict] = []
        for o in cell.get("outputs", []):
            if o.get("output_type") == "stream":
                new_outputs.append(o)
                continue

            if o.get("output_type") in ("execute_result", "display_data"):
                data = o.get("data") or {}
                filtered = {
                    mime: data[mime]
                    for mime in allowed_mimes
                    if mime in data
                }
                if not filtered:
                    continue

                out: dict = {
                    "output_type": o["output_type"],
                    "data": filtered,
                }
                if "execution_count" in o:
                    out["execution_count"] = o["execution_count"]

                if o.get("metadata"):
                    out["metadata"] = o["metadata"]

                new_outputs.append(out)

        cell["outputs"] = new_outputs

    return nb_json


@app.get(
    "/processed",
    summary="List all processed files",
    dependencies=[Security(get_service_key)]
)
async def processed_files():
    return [p.name for p in PROCESSED_DIR.iterdir() if p.is_file()]


@app.get(
    "/processed/{filename}",
    summary="Download a processed file",
    dependencies=[Security(get_service_key)],
)
async def download_processed_file(
    filename: str = PathParam(
        ...,
        description="Exact filename to download"
    ),
):
    file_path = PROCESSED_DIR / filename
    if not file_path.exists():
        raise HTTPException(404, f"'{filename}' not found")
    media_type, _ = guess_type(str(file_path))
    return FileResponse(
        path=str(file_path),
        media_type=media_type or "application/octet-stream",
        filename=filename,
    )


@app.get("/files", response_class=HTMLResponse)
async def processed_files_ui():
    if DEV:
        return """
        <html><body>
            <h1>Processed Files (DEV)</h1>
            <p>(none)</p>
        </body></html>
        """
    files = sorted(
        p.name for p in PROCESSED_DIR.iterdir()
        if p.is_file()
    )
    links = "\n".join(
        f'<li><a href="/processed/{f}">{f}</a></li>' for f in files
    )
    return f"""
    <html><body>
      <h1>Processed Files</h1>
      <ul>{links}</ul>
    </body></html>
    """


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
    client_kwargs = {
        "timeout": 600,
        "kernel_name": "python3",
    }
    client = NotebookClient(nb, **client_kwargs)
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
