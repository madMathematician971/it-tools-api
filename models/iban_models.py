from typing import Optional

from pydantic import BaseModel, Field


class IbanInput(BaseModel):
    iban_string: str = Field(..., description="IBAN string to validate")


class IbanValidationOutput(BaseModel):
    is_valid: bool
    iban_string_formatted: Optional[str] = None
    country_code: Optional[str] = None
    check_digits: Optional[str] = None
    bban: Optional[str] = None
    # Add other components if schwifty provides them easily
    # e.g., bank_code, account_number
    error: Optional[str] = None
