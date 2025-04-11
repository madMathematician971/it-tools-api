from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DiffFormat(str, Enum):
    UNIFIED = "unified"
    CONTEXT = "context"
    HTML = "html"
    NDIFF = "ndiff"


class TextDiffInput(BaseModel):
    text1: str = Field(..., description="First text to compare")
    text2: str = Field(..., description="Second text to compare")
    output_format: DiffFormat = Field(DiffFormat.HTML, description="Output format: html, ndiff, unified, context")
    context_lines: int = Field(3, ge=0, description="Number of context lines for unified/context format")
    ignore_whitespace: bool = Field(False, description="Whether to ignore whitespace differences")


class TextDiffOutput(BaseModel):
    diff: str = Field(..., description="Generated difference between texts")
    format_used: str = Field(..., description="Output format used")
    error: Optional[str] = None
