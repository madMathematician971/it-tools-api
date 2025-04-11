from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SvgInput(BaseModel):
    width: int = Field(..., description="Width of the SVG placeholder", ge=1)
    height: int = Field(..., description="Height of the SVG placeholder", ge=1)
    text: Optional[str] = Field(None, description="Optional text to display")
    bg_color: str = Field("#cccccc", description="Background color (hex)")
    text_color: str = Field("#969696", description="Text color (hex)")
    font_family: str = Field("sans-serif", description="Font family for text")
    font_size: Optional[int] = Field(None, description="Font size (auto-calculated if not provided)", ge=1)

    @field_validator("bg_color", "text_color")
    @classmethod
    def validate_hex_color(cls, v):
        if not v.startswith("#") or len(v) not in [4, 7]:
            raise ValueError("Invalid hex color format (e.g., #ccc or #cccccc)")
        # Add more validation if needed (e.g., check hex chars)
        return v


class SvgOutput(BaseModel):
    svg: str = Field(..., description="Generated SVG placeholder code")
    data_uri: str = Field(..., description="Data URI for the SVG")
    error: Optional[str] = None
