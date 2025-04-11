from pydantic import BaseModel


class EmailInput(BaseModel):
    email: str


class EmailNormalizeOutput(BaseModel):
    normalized_email: str
    original_email: str
