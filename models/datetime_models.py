from typing import Optional, Union

from pydantic import BaseModel, Field


class DateTimeConvertInput(BaseModel):
    input_value: Union[str, int, float] = Field(
        ..., description="Input date/time value (string, unix seconds, unix ms)"
    )
    input_format: str = Field(
        "auto",
        description="Format of the input ('auto', 'unix_s', 'unix_ms', 'iso8601')",
    )
    output_format: str = Field(
        "iso8601",
        description="Target output format ('unix_s', 'unix_ms', 'iso8601', 'rfc2822', 'human_readable', 'custom:<pattern>')",
    )


class DateTimeConvertOutput(BaseModel):
    result: Union[str, int, float]
    input_value: Union[str, int, float]
    input_format: str
    output_format: str
    parsed_utc_iso: Optional[str] = None  # Store the common intermediate representation
