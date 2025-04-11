from typing import Optional

from pydantic import BaseModel, Field


class PhoneInput(BaseModel):
    phone_number_string: str = Field(..., description="Phone number to parse (e.g., +1-202-555-0173, (415) 555‑0132)")
    default_country: Optional[str] = Field(
        None, description="Default country code (e.g., US, GB) if number is ambiguous"
    )


class PhoneOutput(BaseModel):
    is_valid: bool
    parsed_number: Optional[str] = None
    country_code: Optional[int] = None
    national_number: Optional[str] = None
    extension: Optional[str] = None
    country_code_source: Optional[str] = None
    e164_format: Optional[str] = None
    national_format: Optional[str] = None
    international_format: Optional[str] = None
    error: Optional[str] = None
