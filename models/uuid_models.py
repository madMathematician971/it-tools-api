from typing import Optional

from pydantic import BaseModel, Field


class UuidInput(BaseModel):
    namespace: Optional[str] = Field(None, description="Namespace UUID for V3/V5 generation")
    name: Optional[str] = Field(None, description="Name string for V3/V5 generation")


class UuidOutput(BaseModel):
    version: int
    uuid_str: str = Field(..., alias="uuid")


class UuidResponse(BaseModel):
    uuid: str = Field(..., description="Generated UUID")
    version: int = Field(..., description="UUID version (1, 4, etc.)")
    variant: str = Field(..., description="UUID variant")
    is_nil: bool = Field(..., description="Whether the UUID is nil (all zeros)")
    hex: str = Field(..., description="Hexadecimal representation (no dashes)")
    bytes: str = Field(..., description="Bytes representation (as hex)")
    urn: str = Field(..., description="URN representation")
    integer: int = Field(..., description="Integer representation")
    binary: str = Field(..., description="Binary representation")
