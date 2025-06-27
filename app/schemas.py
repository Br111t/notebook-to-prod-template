# app/schemas.py
from pydantic import BaseModel
from typing import List, Any


class NotebookOutputs(BaseModel):
    outputs: List[Any]
