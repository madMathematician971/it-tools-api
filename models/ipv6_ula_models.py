from pydantic import BaseModel, Field


class Ipv6UlaResponse(BaseModel):
    ula_address: str = Field(..., description="Generated IPv6 Unique Local Address (ULA)")
    global_id: str = Field(..., description="40-bit Global ID used (hex)")
    subnet_id: str = Field(..., description="16-bit Subnet ID used (hex)")
