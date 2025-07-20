# test_cli.py
import runpy
import sys

import pandas as pd


def test_analyze_df(monkeypatch):
    from notebook_service.cli import analyze_df

    # get_analysis to return a df eith exactly one new column
    dummy = pd.DataFrame({
        "text": ["foo", "bar"],
        "sentiment": ["pos", "neg"],
    })
    monkeypatch.setattr(
        "notebook_service.cli.get_analysis",
        lambda texts: dummy.copy()
    )

    # original df has a 'textcol' and one other column
    df = pd.DataFrame({
        "textcol": ["foo", "bar"],
        "count": [1, 2],
    })
    out = analyze_df(df, text_column="textcol")

    # should have dropped 'text',
    # kept 'textcol' & 'count', and added 'sentiment'
    assert set(out.columns) == {"textcol", "count", "sentiment"}
    assert out["sentiment"].tolist() == ["pos", "neg"]


def test_main_prints_to_stdout(tmp_path, capsys, monkeypatch):
    from notebook_service.cli import main

    # get_analysis again
    dummy = pd.DataFrame({
        "text": ["cc"],
        "sentiment": ["super"],
    })
    monkeypatch.setattr(
        "notebook_service.cli.get_analysis",
        lambda texts: dummy.copy()
    )

    df = pd.DataFrame({"textcol": ["cc"]})
    in_csv = tmp_path / "in.csv"
    df.to_csv(in_csv, index=False)

    # call main without output path → should print to stdout
    main(str(in_csv), "textcol")
    captured = capsys.readouterr()
    assert "super" in captured.out


def test_main_writes_file(tmp_path, monkeypatch):
    from notebook_service.cli import main
    dummy = pd.DataFrame({
        "text": ["qq"],
        "sentiment": ["amazing"],
    })
    monkeypatch.setattr(
        "notebook_service.cli.get_analysis",
        lambda text: dummy.copy()
    )

    df = pd.DataFrame({"textcol": ["qq"]})
    in_csv = tmp_path / "in.csv"
    df.to_csv(in_csv, index=False)
    out_csv = tmp_path / "out.csv"

    # call main with an output path → should write CSV
    main(str(in_csv), "textcol", str(out_csv))
    assert out_csv.exists()
    df_out = pd.read_csv(out_csv)
    assert "sentiment" in df_out.columns


def test_cli_as_script_stdout(tmp_path, capsys, monkeypatch):
    import notebook_service.emotion as emo

    # 1) Stub the *source* of get_analysis
    fake_df = pd.DataFrame({"text": ["foo"], "sentiment": ["bar"]})
    # import the module so that sys.modules["notebook_service.emotion"] exists
    monkeypatch.setattr(emo, "get_analysis", lambda texts: fake_df.copy())

    # 2) Prepare input CSV
    in_csv = tmp_path / "in.csv"
    pd.DataFrame({"textcol": ["foo"]}).to_csv(in_csv, index=False)

    # 3) Set up sys.argv for the script
    monkeypatch.setattr(sys, "argv", [
        "notebook_service.cli",
        "--input", str(in_csv),
        "--column", "textcol",
    ])

    # Ensure we load a fresh cli module under __main__
    sys.modules.pop("notebook_service.cli", None)

    # 4) Run the module as a script —
    # it will import our stubbed emo.get_analysis
    runpy.run_module(
        "notebook_service.cli",
        run_name="__main__",
        alter_sys=True
    )

    captured = capsys.readouterr()
    assert "bar" in captured.out


def test_cli_as_script_write(tmp_path, monkeypatch):
    import notebook_service.emotion as emo

    # Stub emotion.get_analysis again
    fake_df = pd.DataFrame({"text": ["baz"], "sentiment": ["qux"]})
    monkeypatch.setattr(emo, "get_analysis", lambda texts: fake_df.copy())

    # Prepare files
    in_csv = tmp_path / "in.csv"
    pd.DataFrame({"textcol": ["baz"]}).to_csv(in_csv, index=False)
    out_csv = tmp_path / "out.csv"

    # Simulate CLI args
    monkeypatch.setattr(sys, "argv", [
        "notebook_service.cli",
        "--input", str(in_csv),
        "--column", "textcol",
        "--output", str(out_csv),
    ])

    # Ensure we load a fresh cli module under __main__
    sys.modules.pop("notebook_service.cli", None)

    # Execute
    runpy.run_module(
        "notebook_service.cli",
        run_name="__main__",
        alter_sys=True
    )

    # Assert file was written with our stubbed sentiment
    assert out_csv.exists()
    df_out = pd.read_csv(out_csv)
    assert df_out["sentiment"].tolist() == ["qux"]
