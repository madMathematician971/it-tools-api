from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class JwtInput(BaseModel):
    jwt_string: str = Field(..., description="The JWT string to decode.")
    secret_or_key: Optional[str] = Field(
        None, 
        description="The secret (for HS*) or public key (for RS*/ES*) for signature verification.",
    )
    algorithms: Optional[List[str]] = Field(
        None,
        description="List of allowed algorithms (e.g., ['HS256', 'HS512']). Required if verifying.",
    )


class JwtOutput(BaseModel):
    header: Optional[dict[str, Any]] = Field(None, description="Decoded JWT header.")
    payload: Optional[dict[str, Any]] = Field(None, description="Decoded JWT payload.")
    signature_verified: Optional[bool] = Field(
        None,
        description="Whether the signature was successfully verified (True/False) or verification was not attempted (None).",
    )
    error: Optional[str] = Field(None, description="Error message if parsing or verification failed.")

    @field_validator("header", "payload", mode="before")
    def empty_dict_to_none(cls, value):
        # Ensure empty dicts are treated as None for consistency if needed,
        return value if value else None
