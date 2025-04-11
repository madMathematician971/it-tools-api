import re
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator


class RomanEncodeInput(BaseModel):
    number: int = Field(..., description="Integer to convert to Roman numerals (1-3999)", ge=1, le=3999)


class RomanDecodeInput(BaseModel):
    roman_numeral: str = Field(..., description="Roman numeral string to convert to integer")

    @field_validator("roman_numeral")
    @classmethod
    def validate_roman_numeral(cls, v):
        # Basic validation for allowed characters and basic structure
        if not re.match(r"^[MDCLXVI]+$", v.upper()):
            raise ValueError("Invalid characters in Roman numeral")
        # Add more complex validation if needed (e.g., subtractive rules)
        return v.upper()


class RomanOutput(BaseModel):
    input_value: Union[int, str] = Field(..., description="Original input (integer or Roman numeral)")
    result: Union[str, int] = Field(..., description="Conversion result (Roman numeral or integer)")
    error: Optional[str] = None
