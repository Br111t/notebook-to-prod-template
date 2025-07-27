# tests/notebook_service/test_emotion.py
import importlib
import os
import sys

import pandas as pd
import pytest


def reload_emotion(dev_mode: bool):
    """
    Helper to (re)load the emotion module under a given DEV_MODE setting.
    """
    # 1) Ensure the env var is set
    os.environ["DEV_MODE"] = "true" if dev_mode else "false"

    # 2) Remove any cached module so importlib.reload actually
    # re‑executes __init__
    sys.modules.pop("notebook_service.emotion", None)

    # 3) Import & reload
    import notebook_service.emotion as emo
    importlib.reload(emo)
    return emo


def test_get_analysis_empty_list_dev(monkeypatch):
    emo = reload_emotion(dev_mode=True)
    df = emo.get_analysis([])
    # empty input → empty DataFrame
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_get_analysis_dummy_stub_outputs(monkeypatch):
    emo = reload_emotion(dev_mode=True)

    # Call with two sample texts
    df = emo.get_analysis(["hello", "world"])

    # Should have exactly these columns
    expected_cols = [
        "text",
        "anger", "disgust", "fear", "joy", "sadness",
        "concepts_raw", "concepts", "semantic_roles",
    ]
    assert list(df.columns) == expected_cols

    # DummyNLU stub sets joy=1.0, others=0.0, and no concepts/roles
    assert all(df["joy"] == 1.0)
    assert all(df["anger"] == 0.0)
    assert all(df["concepts_raw"].apply(lambda x: x == []))
    assert all(df["concepts"].apply(lambda x: x == []))
    assert all(df["semantic_roles"].apply(lambda x: x == []))


def test_get_analysis_real_path_parses_concepts_and_roles(monkeypatch):
    # Switch to “real” mode
    emo = reload_emotion(dev_mode=False)

    # Build a fake “raw” response
    # containing emotion + concepts + semantic_roles
    fake_raw = {
        "emotion": {
            "document": {"emotion": {
                "anger": 0.2, "disgust": 0.3, "fear": 0.4,
                "joy": 0.5, "sadness": 0.6
            }}
        },
        "concepts": [
            {"text": "Alpha"}, {"text": "Beta"}
        ],
        "semantic_roles": [
            {
                "subject": {"text": "Brittany"},
                "action": {"text": "writes"},
                "object": {"text": "code"},
            }
        ],
    }

    # Stub NLU_CLIENT.analyze(...) so it returns an object with get_result()
    class FakeResp:
        def get_result(self):
            return fake_raw

    monkeypatch.setattr(
        emo.NLU_CLIENT,
        "analyze",
        lambda *args, **kwargs: FakeResp()
    )

    # Now run get_analysis
    df = emo.get_analysis(["some text"])

    # Verify the same columns
    expected_cols = [
        "text",
        "anger", "disgust", "fear", "joy", "sadness",
        "concepts_raw", "concepts", "semantic_roles",
    ]
    assert list(df.columns) == expected_cols

    row = df.iloc[0]
    assert row["text"] == "some text"
    # emotion values should match fake_raw
    assert pytest.approx(row["anger"], rel=1e-6) == 0.2
    assert pytest.approx(row["joy"],   rel=1e-6) == 0.5

    # concepts_raw is the full list of dicts
    assert row["concepts_raw"] == fake_raw["concepts"]
    # concepts is just the text values
    assert row["concepts"] == ["Alpha", "Beta"]
    # semantic_roles is list of tuples
    assert row["semantic_roles"] == [("Brittany", "writes", "code")]
