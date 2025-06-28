# notebook_service/test_emotion.py
# is pure‐function (unit) tests of your emotion helpers.
import importlib

import pandas as pd
import pytest

import notebook_service.emotion as emotion_module

pytest.skip("Not ready yet", allow_module_level=True)


@pytest.fixture(autouse=True)
def set_dev_mode(monkeypatch):
    # Ensure DEV_MODE is true so we use the dummy stub
    monkeypatch.setenv("DEV_MODE", "true")
    # Reload the module to pick up the DEV_MODE change
    importlib.reload(emotion_module)


def test_get_analysis_returns_dataframe():
    texts = ["hello", "world"]
    df = emotion_module.get_analysis(texts)
    expected_cols = [
        "text",
        "anger",
        "disgust",
        "fear",
        "joy",
        "sadness",
        "concepts",
        "semantic_roles",
    ]
    assert list(df.columns) == expected_cols
    assert df.shape == (2, len(expected_cols))

    # Dummy stub: joy=1.0, others=0.0; concepts & semantic_roles empty
    assert all(df["joy"] == 1.0)
    assert all(df["anger"] == 0.0)
    assert all(df["concepts"].apply(lambda x: x == []))
    assert all(df["semantic_roles"].apply(lambda x: x == []))


def test_get_analysis_empty_list():
    df = emotion_module.get_analysis([])
    assert isinstance(df, pd.DataFrame)
    assert df.empty
