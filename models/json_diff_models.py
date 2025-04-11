from typing import Optional

from pydantic import BaseModel, Field


class JsonDiffInput(BaseModel):
    json1: str = Field(..., description="First JSON string")
    json2: str = Field(..., description="Second JSON string")
    ignore_order: bool = Field(False, description="Whether to ignore array order")
    output_format: str = Field("delta", description="Output format: delta (detailed), simple (list of changes)")


class JsonDiffOutput(BaseModel):
    diff: str = Field(..., description="Generated JSON diff")
    format_used: str = Field(..., description="Output format used")
    error: Optional[str] = None
