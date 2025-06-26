# tests/test_emotion.py
import pandas as pd
import pytest
from src.emotion import get_emotions, analyze_emotion

class DummyTone:
    def tone(self, payload, content_type):
        return {"document_tone": {"tones": [
            {"tone_name": "Joy", "score": 0.9},
            {"tone_name": "Sadness", "score": 0.1},
        ]}}

@pytest.fixture(autouse=True)
def patch_tone_analyzer(monkeypatch):
    # Replace the real analyzer with our dummy
    monkeypatch.setattr("src.emotion.tone_analyzer", DummyTone())
    yield

def test_analyze_emotion_returns_dict():
    result = analyze_emotion("Hello world")
    assert "document_tone" in result
    assert isinstance(result["document_tone"]["tones"], list)

def test_get_emotions_dataframe():
    texts = ["foo", "bar"]
    df = get_emotions(texts)
    # Should have three columns: text, Joy, Sadness
    assert list(df.columns) == ["text", "Joy", "Sadness"]
    assert df.shape == (2, 3)
    assert all(df["Joy"] == 0.9)
    assert all(df["Sadness"] == 0.1)

def test_get_emotions_empty_list():
    df = get_emotions([])
    assert isinstance(df, pd.DataFrame)
    assert df.empty
