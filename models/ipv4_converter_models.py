from typing import Optional

from pydantic import BaseModel, Field, field_validator


class IPv4Input(BaseModel):
    ip_address: str = Field(..., description="IPv4 address to convert (dotted decimal, decimal, hex, or binary)")
    format: Optional[str] = Field(None, description="Format hint: decimal, dotted, hex, binary")

    @field_validator("format")
    @classmethod
    def validate_format(cls, v):
        if v and v not in ["decimal", "dotted", "hex", "binary"]:
            raise ValueError("Format must be one of: decimal, dotted, hex, binary")
        return v


class IPv4Output(BaseModel):
    original: str = Field(..., description="Original input")
    dotted_decimal: str = Field(..., description="Dotted decimal notation (e.g., 192.168.1.1)")
    decimal: int = Field(..., description="Decimal notation (e.g., 3232235777)")
    hexadecimal: str = Field(..., description="Hexadecimal notation (e.g., 0xC0A80101)")
    binary: str = Field(..., description="Binary notation (e.g., 11000000101010000000000100000001)")
    error: Optional[str] = None
