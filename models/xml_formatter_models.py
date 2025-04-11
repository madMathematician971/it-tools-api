from typing import Optional

from pydantic import BaseModel, Field


class XmlInput(BaseModel):
    xml: str = Field(..., description="XML string to format/prettify")
    indent: str = Field("  ", description="Indentation to use (spaces or tabs)")
    preserve_whitespace: bool = Field(False, description="Whether to preserve whitespace in text nodes")
    omit_declaration: bool = Field(False, description="Whether to omit XML declaration")
    encoding: str = Field("utf-8", description="Encoding to use in XML declaration")


class XmlOutput(BaseModel):
    original: str = Field(..., description="Original XML input")
    formatted: str = Field(..., description="Formatted/prettified XML")
    error: Optional[str] = None
