from pydantic import BaseModel


class HashInput(BaseModel):
    text: str


class HashOutput(BaseModel):
    md5: str
    sha1: str
    sha256: str
    sha512: str
