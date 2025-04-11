import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# Basic MAC address regex (allows common delimiters and different lengths for OUI/full MAC)
MAC_REGEX = re.compile(r"^([0-9A-Fa-f]{2}[:\-.]?){2,5}[0-9A-Fa-f]{2}$")


class MacLookupInput(BaseModel):
    mac_address: str = Field(..., description="MAC address to lookup (e.g., 00:1A:2B... or 001A2B)")

    @field_validator("mac_address")
    @classmethod
    def validate_mac_format(cls, v):
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("MAC address cannot be empty")
        if not MAC_REGEX.match(v_clean):
            raise ValueError(f"Invalid MAC address format: '{v_clean}'")
        return v_clean  # Return cleaned string, normalization happens in router


class MacLookupOutput(BaseModel):
    oui: Optional[str] = Field(None, description="OUI part of the MAC address (first 6 hex digits)")
    company: Optional[str] = Field(None, description="Company/Vendor name associated with the OUI")
    is_private: Optional[bool] = Field(None, description="Whether the MAC address is locally administered (private)")
    error: Optional[str] = None
