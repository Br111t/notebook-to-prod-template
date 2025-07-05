import os
from typing import Any, Dict, List, Tuple

import pandas as pd
from dotenv import load_dotenv

load_dotenv()
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

if DEV_MODE:
    # dummy stub
    class DummyNLU:
        def analyze(self, *, text: str, features: Any):
            return {
                "emotion": {
                    "document": {
                        "emotion": {
                            "anger": 0.0,
                            "disgust": 0.0,
                            "fear": 0.0,
                            "joy": 1.0,
                            "sadness": 0.0,
                        }
                    }
                },
                # no concepts/semantic_roles in dev
            }

    NLU_CLIENT = DummyNLU()

else:
    from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
    from ibm_watson import NaturalLanguageUnderstandingV1
    from ibm_watson.natural_language_understanding_v1 import (
        ConceptsOptions,
        EmotionOptions,
        Features,
        SemanticRolesOptions,
    )

    auth = IAMAuthenticator(os.environ["NLU_APIKEY"])
    NLU_CLIENT = NaturalLanguageUnderstandingV1(
        version="2023-08-01", authenticator=auth
    )
    NLU_CLIENT.set_service_url(os.environ["NLU_URL"])


def get_analysis(texts: List[str]) -> pd.DataFrame:
    """
    Run NLU with Concepts, Semantic Roles, and Emotion on each text.
    Returns a DataFrame with columns:
      text, anger, disgust, fear, joy, sadness,
      concepts (List[str]), semantic_roles (List[Tuple[str,str,str]])
    """
    records: List[Dict[str, Any]] = []

    for txt in texts:
        if DEV_MODE:
            raw = NLU_CLIENT.analyze(text=txt, features=None)
        else:
            raw = NLU_CLIENT.analyze(
                text=txt,
                features=Features(
                    concepts=ConceptsOptions(limit=8),
                    semantic_roles=SemanticRolesOptions(limit=5),
                    emotion=EmotionOptions(),
                ),
                return_analyzed_text=False,
            ).get_result()

        # parse emotion
        emo = raw["emotion"]["document"]["emotion"]

        # keep full raw concepts
        concepts_raw = raw.get("concepts", [])

        # extract just the text for your existing pipeline
        concepts = [c["text"] for c in concepts_raw]

        # parse semantic roles
        roles: List[Tuple[str, str, str]] = []
        for r in raw.get("semantic_roles", []):
            subj = r["subject"]["text"]
            act = r["action"]["text"]
            obj = r.get("object", {}).get("text", "")
            roles.append((subj, act, obj))

        records.append({
            "text": txt,
            **emo,
            "concepts_raw": concepts_raw,
            "concepts": concepts,
            "semantic_roles": roles,
        })

    return pd.DataFrame.from_records(records)
