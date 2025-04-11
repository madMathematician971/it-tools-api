from pydantic import BaseModel, Field


class JsonTextInput(BaseModel):
    json_string: str = Field(..., description="JSON data as a string")


class JsonFormatInput(BaseModel):
    json_string: str
    indent: int = Field(4, ge=0, description="Indentation level (e.g., 2, 4)")
    sort_keys: bool = Field(False, description="Whether to sort keys alphabetically")


class JsonOutput(BaseModel):
    result_string: str
    error: str | None = None  # Optional error message
