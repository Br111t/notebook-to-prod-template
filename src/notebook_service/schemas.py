# app/schemas.py
from typing import Any, List

from pydantic import BaseModel


class NotebookOutputs(BaseModel):
    outputs: List[Any]
