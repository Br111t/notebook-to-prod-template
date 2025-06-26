from fastapi import FastAPI, HTTPException
from pathlib import Path
from src.runner import run_notebook
from src.emotion import get_emotions

app = FastAPI(
    title="Notebook-to-API",
    description="Execute Jupyter notebooks via REST and analyze text emotions via IBM Watson.",
    version="0.1.0"
)


@app.get("/run/{notebook_name}", tags=["execution"])
async def run_notebook_endpoint(notebook_name: str):
    """
    Execute the given notebook (by name, without .ipynb) and return its output.
    """
    path = Path("notebooks") / f"{notebook_name}.ipynb"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Notebook `{notebook_name}` not found")
    return run_notebook(str(path))


@app.post("/analyze-emotions", tags=["nlp"])
async def analyze_emotions_endpoint(payload: dict):
    """
    Analyze a list of text entries for emotional tone.

    Request body: { "texts": ["text1", "text2", ...] }
    Response: List of { text: str, Tone1: float, Tone2: float, ... }
    """
    texts = payload.get("texts")
    if not isinstance(texts, list):
        raise HTTPException(status_code=400, detail="Payload must include a list of texts under `texts`")
    df = get_emotions(texts)
    return df.to_dict(orient="records")


