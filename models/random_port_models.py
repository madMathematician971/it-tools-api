from typing import Optional

from pydantic import BaseModel, Field


class PortResponse(BaseModel):
    port: int = Field(..., description="Generated random port number")
    range_type: str = Field(..., description="Type of range (e.g., well-known, registered, ephemeral)")
    service_name: Optional[str] = Field(None, description="Common service name if port is well-known")
