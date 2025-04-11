from pydantic import BaseModel, Field


class CryptoInput(BaseModel):
    text: str
    password: str
    algorithm: str = Field("aes-256-cbc", description="Currently only supports 'aes-256-cbc'")


class CryptoEncryptOutput(BaseModel):
    ciphertext: str  # Base64 encoded: salt + iv + encrypted_data


class CryptoDecryptInput(BaseModel):
    ciphertext: str  # Base64 encoded: salt + iv + encrypted_data
    password: str
    algorithm: str = Field("aes-256-cbc", description="Currently only supports 'aes-256-cbc'")


class CryptoDecryptOutput(BaseModel):
    plaintext: str
