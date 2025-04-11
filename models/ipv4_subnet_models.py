from typing import Optional

from pydantic import BaseModel, Field


class Ipv4SubnetInput(BaseModel):
    ip_cidr: str = Field(
        ...,
        description="IPv4 address with CIDR prefix (e.g., 192.168.1.50/24) or IP and mask (e.g., 192.168.1.50/255.255.255.0)",
    )


class Ipv4SubnetOutput(BaseModel):
    network_address: Optional[str] = Field(None, description="Network address of the subnet.")
    broadcast_address: Optional[str] = Field(None, description="Broadcast address of the subnet.")
    netmask: Optional[str] = Field(None, description="Subnet mask.")
    cidr_prefix: Optional[int] = Field(None, description="CIDR prefix length.")
    num_addresses: Optional[int] = Field(None, description="Total number of IP addresses in the subnet.")
    num_usable_hosts: Optional[int] = Field(None, description="Number of usable host addresses in the subnet.")
    first_usable_host: Optional[str] = Field(None, description="First usable host IP address.")
    last_usable_host: Optional[str] = Field(None, description="Last usable host IP address.")
    is_private: Optional[bool] = Field(None, description="Indicates if the network is private (RFC 1918).")
    is_multicast: Optional[bool] = Field(None, description="Indicates if the network is multicast.")
    is_loopback: Optional[bool] = Field(None, description="Indicates if the network is loopback.")
    error: Optional[str] = Field(None, description="Error message if calculation failed.")
