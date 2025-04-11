from typing import Optional

from pydantic import BaseModel, Field


class MacResponse(BaseModel):
    mac_address: str = Field(..., description="Generated MAC address")
    format: str = Field(..., description="Format of the MAC address")
    type: str = Field(..., description="Type (unicast/multicast)")
    locality: str = Field(..., description="Locality (universal/local)")
    company: Optional[str] = Field(None, description="Vendor/Company name if OUI is universal and found")
