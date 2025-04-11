from pydantic import BaseModel, Field


class HmacInput(BaseModel):
    text: str
    key: str  # Secret key
    algorithm: str = Field("sha256", description="Hash algorithm (e.g., md5, sha1, sha256, sha512)")
    # Add encoding options if needed


class HmacOutput(BaseModel):
    hmac_hex: str
