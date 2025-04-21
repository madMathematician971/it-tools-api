"""
Pydantic models for the List Converter tool and router.
"""

from pydantic import BaseModel, Field


class ListConverterInput(BaseModel):
    input_text: str = Field(..., description="The list text to convert.")
    input_format: str = Field(
        ...,
        description="Format of the input list (comma, newline, space, semicolon, bullet_asterisk, bullet_hyphen, numbered_dot, numbered_paren).",
    )
    output_format: str = Field(
        ...,
        description="Desired format for the output list (comma, newline, space, semicolon, bullet_asterisk, bullet_hyphen, numbered_dot, numbered_paren).",
    )
    ignore_empty: bool = Field(True, description="Ignore empty lines or items during conversion.")
    trim_items: bool = Field(True, description="Trim whitespace from each list item.")


class ListConverterOutput(BaseModel):
    result: str = Field(..., description="The list converted to the desired output format.")
