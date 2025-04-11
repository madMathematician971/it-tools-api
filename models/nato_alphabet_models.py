from typing import Dict

from pydantic import BaseModel, Field


class NatoInput(BaseModel):
    text: str = Field(..., description="Text to convert to NATO phonetic alphabet")
    format: str = Field("table", description="Output format (table, list, text)")
    separator: str = Field(", ", description="Separator for text format output")
    include_original: bool = Field(True, description="Include original character in output")
    lowercase: bool = Field(False, description="Convert result to lowercase")


class NatoOutput(BaseModel):
    input: str = Field(..., description="Original input text")
    output: str = Field(..., description="Converted NATO phonetic text")
    format: str = Field(..., description="Output format used")
    character_map: Dict[str, str] = Field(..., description="Mapping of characters to NATO words")
