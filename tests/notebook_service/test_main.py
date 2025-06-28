# ensures your API layer works.
# integration—spinning up the FastAPI
# endpoint and hitting it via TestClient.
import pytest


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


# def test_run_endpoint(client, tmp_path, sample_notebook,
# notebook_name, status_code):

#     sample_notebook(tmp_path)

#     # Compute PROJECT_ROOT/tests/notebook_service → climb two levels up
#     project_root = Path(__file__).resolve().parents[2]
#     nb_src = project_root / "notebooks" / "example.ipynb"

#     # Copy the notebook into a temp dir so run_notebook can open it
#     nb_copy = tmp_path / "example.ipynb"
#     nb_copy.write_bytes(nb_src.read_bytes())

#     path = f"/run/{notebook_name}"
#     resp = client.get(path)
#     assert resp.status_code == status_code
