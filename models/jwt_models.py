import json
from typing import Any

from pydantic import BaseModel, Field, field_validator


class JwtInput(BaseModel):
    jwt_string: str = Field(..., description="The JWT string to decode.")
    secret_or_key: str | None = Field(
        None,
        description="The secret (for HS*) or public key (for RS*/ES*) for signature verification.",
    )
    algorithms: list[str] | None = Field(
        None,
        description="List of allowed algorithms (e.g., ['HS256', 'HS512']). Required if verifying.",
    )


class JwtOutput(BaseModel):
    header: dict[str, Any] | None = Field(None, description="Decoded JWT header.")
    payload: dict[str, Any] | None = Field(None, description="Decoded JWT payload.")
    signature_verified: bool | None = Field(
        None,
        description="Whether the signature was successfully verified (True/False) or verification was not attempted (None).",
    )
    error: str | None = Field(None, description="Error message if parsing or verification failed.")

    @field_validator("header", "payload", mode="before")
    @classmethod
    def _validate_json(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON string")
        return v

    @field_validator("header", "payload", mode="before")
    @classmethod
    def empty_dict_to_none(cls, value):
        if value == {}:
            return None
        return value
