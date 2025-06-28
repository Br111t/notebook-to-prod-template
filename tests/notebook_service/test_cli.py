import subprocess

import pandas as pd
import pytest
from click.testing import CliRunner

from notebook_service.cli import analyze_df, main

pytest.skip("Not ready yet", allow_module_level=True)


def test_analyze_df_groups_and_sums():
    df = pd.DataFrame(
        {
            "col1": [1, 2, 3],
            "col2": ["a", "b", "a"],
            "value": [10, 20, 30],
        }
    )
    result = analyze_df(df, group_by="col2", agg="sum")
    assert isinstance(result, pd.DataFrame)
    summed = result.set_index("col2")["value"].to_dict()
    assert summed == {"a": 40, "b": 20}


def test_cli_end_to_end(tmp_path):
    df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    input_csv = tmp_path / "in.csv"
    df.to_csv(input_csv, index=False)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "analyze",
            "--input",
            str(input_csv),
            "--group-by",
            "y",
            "--agg",
            "sum",
        ],
    )
    assert result.exit_code == 0
    # adjust this assertion to your real CLI output
    assert "y" in result.output and "7" in result.output


def test_cli_subprocess(tmp_path):
    df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    input_csv = tmp_path / "in.csv"
    df.to_csv(input_csv, index=False)

    cmd = [
        "python",
        "-m",
        "notebook_service.cli",
        "--input",
        str(input_csv),
        "--group-by",
        "y",
        "--agg",
        "sum",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "y" in proc.stdout and "7" in proc.stdout
