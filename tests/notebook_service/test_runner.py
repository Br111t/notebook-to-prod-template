import importlib
from types import SimpleNamespace

import nest_asyncio
import pandas as pd
import pytest

import notebook_service.runner as runner_mod
from notebook_service.runner import load_data, run_notebook

# Ensure notebooks run in the temp dir
nest_asyncio.apply()


def reload_runner(tmp_path):
    """
    Reload the runner module so NOTEBOOK_DIR is reset to tmp_path
    """
    import notebook_service.runner as runner_module
    importlib.reload(runner_module)
    runner_module.NOTEBOOK_DIR = tmp_path
    return runner_module


def test_load_data(tmp_path):
    runner = reload_runner(tmp_path)
    # Create a sample CSV
    in_csv = tmp_path / "data.csv"
    df = pd.DataFrame({"entry": ["A", "B"]})
    df.to_csv(in_csv, index=False)

    out = runner.load_data(str(in_csv))
    assert list(out.columns) == ["entry"]
    assert out.shape == (2, 1)


def test_run_notebook_file_not_found(tmp_path):
    runner = reload_runner(tmp_path)
    with pytest.raises(FileNotFoundError):
        runner.run_notebook("does_not_exist")


def test_load_data_reads_csv(tmp_path):
    # Create a tiny CSV
    csv = tmp_path / "data.csv"
    csv.write_text("x,y\n10,20\n30,40\n")
    df = load_data(str(csv))
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["x", "y"]
    assert df.iloc[0].to_dict() == {"x": 10, "y": 20}


def test_run_notebook_adds_suffix_and_stream_and_execute(
        tmp_path,
        monkeypatch,
        dummy_nb):
    # 1) Create foo.ipynb
    nb_file = tmp_path / "foo.ipynb"
    nb_file.write_text("")

    # Stub out read() and execute() to return our dummy
    monkeypatch.setattr(
        runner_mod.nbformat,
        "read",
        lambda path,
        **kwargs: dummy_nb
    )
    monkeypatch.setattr(
        runner_mod,
        "execute",
        lambda nb,
        **kw: dummy_nb)

    # Now exercise run_notebook
    result = run_notebook("foo")   # no suffix
    outputs = result["outputs"]

    assert {
        "cell": 1,
        "type": "stream",
        "mime": "text/plain",
        "data": "seq1"
    } in outputs
    assert {
        "cell": 1,
        "type": "display_data",
        "mime": "text/plain",
        "data": "seq2"
    } in outputs
    assert len(outputs) == 2


def test_run_notebook_filters_allowed_mimes(tmp_path, monkeypatch):
    # 1) Create an empty baz.ipynb so resolve(strict=True) passes
    nb_file = tmp_path / "baz.ipynb"
    nb_file.write_text("")

    # 2) Build a simple dummy with the mixed‑mime outputs
    dummy = SimpleNamespace(cells=[{
        "outputs": [
            {
                "output_type": "display_data",
                "data": {"application/json": {"foo": 1}}
            },
            {
                "output_type": "display_data",
                "data": {"text/plain": "text"}
            },
            {
                "output_type": "display_data",
                "data": {"image/png": "iVBORw0KG"}
            },
            # disallowed
            {
                "output_type": "display_data",
                "data": {"application/pdf":  b"%PDF-"}
            },
        ]
    }])

    # 3) Stub both read() and execute() to return our dummy (no validation)
    monkeypatch.setattr(
        runner_mod.nbformat,
        "read",
        lambda path, **kwargs: dummy
    )
    monkeypatch.setattr(
        runner_mod,
        "execute",
        lambda nb, **kw: dummy
    )

    # 4) Run and inspect outputs
    outputs = run_notebook("baz.ipynb")["outputs"]

    # 5) Only the 3 allowed mimes remain
    mimes = {o["mime"] for o in outputs}
    assert mimes == {"application/json", "text/plain", "image/png"}
    assert all(o["type"] == "display_data" for o in outputs)
    assert all(o["cell"] == 1 for o in outputs)
    assert len(outputs) == 3
