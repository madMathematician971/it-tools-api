from pydantic import BaseModel, Field


class AsciiTextDrawerRequest(BaseModel):
    text: str = Field(..., description="The text to convert to ASCII art")
    font: str = Field(
        "standard",
        description="Font to use for ASCII art generation",
    )
    alignment: str = Field("left", description="Text alignment (left, center, right)")


class AsciiTextDrawerResponse(BaseModel):
    ascii_art: str = Field(..., description="The generated ASCII art")
    font_used: str = Field(..., description="The font used for generation")
    alignment: str = Field(..., description="The alignment used")
