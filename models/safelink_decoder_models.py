from typing import Optional

from pydantic import BaseModel, Field


class SafelinkInput(BaseModel):
    url: str = Field(..., description="URL to decode")


class SafelinkOutput(BaseModel):
    original_url: str = Field(..., description="Original input URL")
    decoded_url: Optional[str] = None
    decoding_method: Optional[str] = None
    error: Optional[str] = None
