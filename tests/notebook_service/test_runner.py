# unit—test exercising your run_notebook library logic.
import pandas as pd
import pytest

from notebook_service.graph_builder import preprocess_concepts
from notebook_service.runner import load_data

pytest.skip("Not ready yet", allow_module_level=True)


def test_load_data_schema(tmp_path, sample_csv):
    # sample_csv is a fixture writing a small CSV with known columns
    path = sample_csv(tmp_path, ["entry"], [["Test"]])
    df = load_data(str(path))
    assert list(df.columns) == ["entry"]
    assert df.shape == (1, 1)


def test_preprocess_adds_columns():
    df = pd.DataFrame({"entry": ["I am grateful", "I am happy"]})
    df2 = preprocess_concepts(df)
    assert "clean_text" in df2.columns
    assert "concepts" in df2.columns


# def test_example_notebook_runs(tmp_path):
#     # Compute PROJECT_ROOT/tests/notebook_service → climb two levels up
#     project_root = Path(__file__).resolve().parents[2]
#     nb_src = project_root / "notebooks" / "example.ipynb"

#     # Copy the notebook into a temp dir so run_notebook can open it
#     nb_copy = tmp_path / "example.ipynb"
#     nb_copy.write_bytes(nb_src.read_bytes())

#     result = run_notebook(str(nb_copy))
#     # We know example.ipynb prints "4\n" in its last cell:
#     assert any("4" in out for out in result["outputs"])
