# app/schemas.py
from enum import Enum
from typing import Any

from pydantic import BaseModel


class OutputType(str, Enum):
    stream = "stream"
    execute_result = "execute_result"
    display_data = "display_data"


class CellOutput(BaseModel):
    cell: int
    type: OutputType
    mime: str
    data: Any


class NotebookOutputs(BaseModel):
    outputs: list[CellOutput]
