from typing import Optional, Union

from pydantic import BaseModel, Field


class ColorConvertInput(BaseModel):
    input_color: str = Field(
        ...,
        description="Input color string in any supported format (hex, rgb, hsl, web names, etc.)",
    )
    target_format: str = Field(
        ...,
        description="Target format (e.g., hex, hex_verbose, rgb, hsl, hsv, web, luminance)",
    )


class ColorConvertOutput(BaseModel):
    result: Union[str, float]  # Result can be string or float (for luminance)
    input_color: str
    target_format: str
    parsed_hex: Optional[str] = None
    parsed_rgb: Optional[str] = None
    parsed_hsl: Optional[str] = None
