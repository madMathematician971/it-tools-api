from typing import Dict, Optional

from pydantic import BaseModel, Field


class TextBinaryInput(BaseModel):
    text: str = Field(..., description="Text to convert to binary or binary to decode")
    mode: str = Field(..., description="Conversion mode: text_to_binary or binary_to_text")
    include_spaces: bool = Field(True, description="Include spaces between binary values")
    space_replacement: str = Field("00100000", description="Binary representation to use for spaces")


class TextBinaryOutput(BaseModel):
    original: str = Field(..., description="Original input")
    result: str = Field(..., description="Conversion result")
    mode: str = Field(..., description="Mode used for conversion")
    char_mapping: Optional[Dict[str, str]] = None
