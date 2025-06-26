# src/emotion.py
import os
from ibm_watson import ToneAnalyzerV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import pandas as pd
from typing import List

# app/main.py or src/emotion.py (early in the import chain)
from dotenv import load_dotenv

load_dotenv()  # reads .env in the project root

apikey = os.getenv("WATSON_APIKEY")
url    = os.getenv("WATSON_URL")

# In “prod” you’d load the real client
if os.getenv("DEV_MODE", "false").lower() == "true":
    TONE_ANALYZER = None
else:
    from ibm_watson import ToneAnalyzerV3
    from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

    auth = IAMAuthenticator(os.environ[apikey])
    TONE_ANALYZER = ToneAnalyzerV3(
        version="2023-10-01",
        authenticator=auth,
    )
    TONE_ANALYZER.set_service_url(os.environ[url])
	
	
def analyze_emotion(text: str) -> dict:
    if TONE_ANALYZER is None:
        # fallback: return “neutral” for everything
        return {"document_tone": {"tones": [{"tone_name": "Neutral", "score": 0.5}]}}
    
    resp = TONE_ANALYZER.tone({"text": text}, content_type="application/json")
    return resp.get_result()



def get_emotions(entries: List[str]) -> pd.DataFrame:
    """
    Given a list of text entries, returns a pandas DataFrame
    with one row per entry and columns for each detected tone.
    """
    rows = []
    for text in entries:
        result = analyze_emotion(text)
        # flatten the JSON into a dict of tone_name->score
        tones = {
            t["tone_name"]: t["score"]
            for t in result.get("document_tone", {}).get("tones", [])
        }
        tones["text"] = text
        rows.append(tones)

    df = pd.DataFrame(rows).fillna(0.0)
    
    cols = ["text"] + [c for c in df.columns if c != "text"]
    return df[cols]


def get_emotions(entries: List[str]) -> pd.DataFrame:
    rows = []
    for text in entries:
        result = analyze_emotion(text)
        tones = {t["tone_name"]: t["score"] for t in result["document_tone"]["tones"]}
        tones["text"] = text
        rows.append(tones)

    df = pd.DataFrame(rows).fillna(0.0)
    # reorder so ‘text’ is first column
    cols = ["text"] + [c for c in df.columns if c != "text"]
    return df[cols]
