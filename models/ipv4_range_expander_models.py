from pydantic import BaseModel, Field

from mcp_server.tools.ipv4_range_expander import MAX_ADDRESSES_TO_RETURN


class IPv4RangeInput(BaseModel):
    range_input: str = Field(
        ..., description="IPv4 range in CIDR or hyphenated format (e.g., '192.168.1.0/24', '10.0.0.1-10.0.0.10')."
    )
    truncate: bool = Field(
        True, description=f"Whether to truncate the list of IPs if it exceeds {MAX_ADDRESSES_TO_RETURN}."
    )


class IPv4RangeOutput(BaseModel):
    count: int = Field(..., description="Total number of IP addresses in the expanded range.")
    addresses: list[str] = Field(..., description="List of expanded IP addresses.")
    truncated: bool = Field(
        ..., description=f"Indicates if the returned list was truncated to {MAX_ADDRESSES_TO_RETURN} entries."
    )
