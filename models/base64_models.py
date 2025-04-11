from pydantic import BaseModel, Field


class InputString(BaseModel):
    input: str


class OutputString(BaseModel):
    result: str


class Base64DecodeFileRequest(BaseModel):
    base64_string: str = Field(..., description="The Base64 encoded string to decode.")
    filename: str = Field(
        default="decoded_file",
        description="The desired filename for the decoded output.",
    )
