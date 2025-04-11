from pydantic import BaseModel, Field


class BcryptHashInput(BaseModel):
    password: str
    salt_rounds: int = Field(10, ge=4, le=31)


class BcryptHashOutput(BaseModel):
    hash: str


class BcryptVerifyInput(BaseModel):
    password: str
    hash: str


class BcryptVerifyOutput(BaseModel):
    match: bool
