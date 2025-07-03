# ensures your API layer works.
# integration—spinning up the FastAPI
# endpoint and hitting it via TestClient.
import nbformat
import pytest

import notebook_service.runner
from notebook_service.runner import run_notebook


@pytest.mark.parametrize(
    "notebook_name, status_code",
    [
        ("example", 200),  # this notebook *does* exist
        ("does_not_exist", 404),  # this notebook *does not* exist
    ],
)
def test_run_endpoint(
    client, tmp_path, sample_notebook, monkeypatch, notebook_name, status_code
):
    # 1) Tell your app to look in tmp_path:
    monkeypatch.setenv("NOTEBOOK_DIR", str(tmp_path))

    # 2) If we're testing the “exists” case, create the file:
    if notebook_name == "example":
        sample_notebook(name="example")  # writes example.ipynb into tmp_path

    # 3) Call the endpoint:
    resp = client.get(f"/run/{notebook_name}")

    # 4) Assert the expected status:
    assert resp.status_code == status_code


def test_run_notebook_executes_cells(tmp_path):
    # 1) Create a notebook with one code cell that prints "hello world"
    nb = nbformat.v4.new_notebook()
    nb.cells.append(nbformat.v4.new_code_cell("print('hello world')"))
    nbfile = tmp_path / "foo.ipynb"
    nbfile.write_text(nbformat.writes(nb))

    # 2) Call the function directly
    result = run_notebook(nbfile)

    # 3) Assert we saw "hello world" in one of the stream outputs
    outputs = result.get("outputs", [])
    assert outputs, f"No outputs found in {result!r}"

    print("RUNNER FILE:", notebook_service.runner.__file__)

    # each output is a dict with keys 'cell', 'type', 'data'
    stream_data = [o["data"] for o in outputs if o.get("type") == "stream"]
    assert any("hello world" in data for data in stream_data), \
        f"'hello world' not found in stream outputs: {stream_data!r}"
