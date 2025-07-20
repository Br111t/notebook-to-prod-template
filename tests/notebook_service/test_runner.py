import importlib

import nest_asyncio
import pandas as pd
import pytest

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


def test_run_notebook_adds_suffix_and_reads_outputs(tmp_path, monkeypatch):
    runner = reload_runner(tmp_path)
    # Create a dummy notebook file (txt is fine)
    nb_file = tmp_path / "foo.ipynb"
    nb_file.write_text("")

    # Dummy notebook with mixed outputs
    class DummyNB:
        def __init__(self):
            self.cells = [
                {"outputs": [
                    {"output_type": "stream", "text": "seq1"},
                    {"output_type": "display_data", "data":
                     {"text/plain": "seq2"}},
                    {"output_type": "display_data", "data": {}},
                ]}
            ]

    dummy_nb = DummyNB()
    import notebook_service.runner as runner_mod

    # Stub the read & execute calls
    monkeypatch.setattr(
        runner_mod.nbformat,
        "read",
        lambda path,
        as_version: dummy_nb
    )
    monkeypatch.setattr(
        runner_mod,
        "execute",
        lambda nb,
        kernel_name,
        cwd: dummy_nb
    )

    result = runner.run_notebook("foo")
    outputs = result["outputs"]
    assert {"cell": 1, "type": "stream", "data": "seq1"} in outputs
    assert {"cell": 1, "type": "display_data", "data": "seq2"} in outputs
    # the third display_data had no text, so only 2 records
    assert len(outputs) == 2


def test_run_notebook_with_ipynb_and_absolute_path(tmp_path, monkeypatch):
    runner = reload_runner(tmp_path)
    nb_file = tmp_path / "bar.ipynb"
    nb_file.write_text("")

    class DummyNB2:
        def __init__(self):
            self.cells = [
                {"outputs": [{"output_type": "stream", "text": "x"}]}
            ]

    dummy_nb2 = DummyNB2()
    import notebook_service.runner as runner_mod
    monkeypatch.setattr(
        runner_mod.nbformat,
        "read",
        lambda path,
        as_version: dummy_nb2
    )
    monkeypatch.setattr(
        runner_mod,
        "execute",
        lambda nb,
        kernel_name,
        cwd: dummy_nb2
    )

    result = runner.run_notebook(str(nb_file))
    assert result == {"outputs": [{"cell": 1, "type": "stream", "data": "x"}]}


def test_run_notebook_file_not_found(tmp_path):
    runner = reload_runner(tmp_path)
    with pytest.raises(FileNotFoundError):
        runner.run_notebook("does_not_exist")
