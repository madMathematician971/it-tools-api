from typing import Dict, Optional

from pydantic import BaseModel, Field


class UrlParserInput(BaseModel):
    url: str = Field(..., description="URL to parse")


class UrlParserOutput(BaseModel):
    original_url: str = Field(..., description="Original input URL")
    scheme: Optional[str] = None
    netloc: Optional[str] = None
    path: Optional[str] = None
    params: Optional[str] = None
    query: Optional[str] = None
    fragment: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    hostname: Optional[str] = None
    port: Optional[int] = None
    query_params: Optional[Dict[str, list[str]]] = None
    error: Optional[str] = None
