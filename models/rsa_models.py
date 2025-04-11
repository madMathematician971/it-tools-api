from typing import Literal

from pydantic import BaseModel, Field

# Common RSA key sizes
KeySize = Literal[1024, 2048, 4096]


class RsaKeygenInput(BaseModel):
    key_size: KeySize = Field(2048, description="RSA key size in bits (1024, 2048, 4096)")
    # public_exponent: int = Field(65537, description="Public exponent") # Usually fixed


class RsaKeygenOutput(BaseModel):
    private_key_pem: str
    public_key_pem: str
    key_size: int
