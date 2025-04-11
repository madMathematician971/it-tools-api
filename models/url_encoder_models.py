from typing import Optional

from pydantic import BaseModel, Field


class UrlEncoderInput(BaseModel):
    text: str = Field(..., description="Text to encode or decode")
    mode: str = Field(..., description="Operation mode: encode or decode")


class UrlEncoderOutput(BaseModel):
    original: str = Field(..., description="Original input text")
    result: str = Field(..., description="Result of encoding/decoding")
    mode: str = Field(..., description="Operation mode that was used")
    error: Optional[str] = None
