from pydantic import BaseModel, Field


class BaseConvertInput(BaseModel):
    number_string: str = Field(..., description="Number to convert (as string)")
    input_base: int = Field(..., ge=2, le=36, description="Base of the input number (2-36)")
    output_base: int = Field(..., ge=2, le=36, description="Target base for conversion (2-36)")


class BaseConvertOutput(BaseModel):
    result_string: str
    input_number_string: str
    input_base: int
    output_base: int
