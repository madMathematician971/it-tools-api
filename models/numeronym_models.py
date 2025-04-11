from pydantic import BaseModel, Field


class NumeronymInput(BaseModel):
    text: str = Field(..., description="Text to convert to numeronym or vice versa")
    mode: str = Field("convert", description="Mode: convert or decode")


class NumeronymOutput(BaseModel):
    original: str = Field(..., description="Original input text")
    result: str = Field(..., description="Result of conversion/decoding")
    mode: str = Field(..., description="Mode that was used")
