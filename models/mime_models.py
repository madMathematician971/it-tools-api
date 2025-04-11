from typing import List, Optional

from pydantic import BaseModel, Field


class MimeTypeLookupInput(BaseModel):
    extension: str = Field(..., description="File extension (e.g., 'txt', '.json')")


class MimeTypeLookupOutput(BaseModel):
    mime_type: Optional[str] = None
    extension: str


class MimeExtensionLookupInput(BaseModel):
    mime_type: str = Field(..., description="MIME type (e.g., 'text/plain', 'application/json')")


class MimeExtensionLookupOutput(BaseModel):
    extensions: List[str]
    mime_type: str
