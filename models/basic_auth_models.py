from pydantic import BaseModel


class BasicAuthInput(BaseModel):
    username: str
    password: str


class BasicAuthOutput(BaseModel):
    username: str
    password: str
    base64: str
    header: str
