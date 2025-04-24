from pydantic import BaseModel, Field


class NatoInput(BaseModel):
    text: str = Field(..., description="Text to convert to NATO phonetic alphabet")
    output_format: str = Field("text", description="Output format (list, text)")
    separator: str = Field(", ", description="Separator for text format output")
    include_original: bool = Field(True, description="Include original character in output")
    lowercase: bool = Field(False, description="Convert result to lowercase")


class NatoOutput(BaseModel):
    input: str = Field(..., description="Original input text")
    output: str | list[str] = Field(..., description="Converted NATO phonetic text")
    output_format: str = Field(..., description="Output format used")
    character_map: dict[str, str] = Field(..., description="Mapping of characters to NATO words")
