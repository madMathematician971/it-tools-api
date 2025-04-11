from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JwtInput(BaseModel):
    jwt_string: str = Field(..., description="The JWT token string")
    secret_or_key: Optional[str] = Field(
        None,
        description="Optional secret (for HMAC) or public key (for RSA/EC) PEM string for signature verification",
    )
    algorithms: Optional[List[str]] = Field(
        None,
        description="Optional list of allowed algorithms for verification (e.g., ['HS256', 'RS256'])",
    )


class JwtOutput(BaseModel):
    header: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None
    signature_verified: Optional[bool] = None
    error: Optional[str] = None
