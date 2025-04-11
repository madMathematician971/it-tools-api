from pydantic import BaseModel, Field


class Bip39Input(BaseModel):
    word_count: int = Field(12, description="Number of words (12, 15, 18, 21, 24)")
    language: str = Field("english", description="Language (currently only english supported by library)")


class Bip39Output(BaseModel):
    mnemonic: str
    word_count: int
    language: str
