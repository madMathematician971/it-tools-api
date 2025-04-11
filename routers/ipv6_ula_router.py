import ipaddress
import logging
import secrets
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from models.ipv6_ula_models import Ipv6UlaResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ipv6-ula", tags=["IPv6 ULA Generator"])


@router.get("/", response_model=Ipv6UlaResponse)
async def generate_ipv6_ula(
    global_id: Optional[str] = Query(
        None,
        title="Global ID",
        description="Optional 10-character hexadecimal Global ID (e.g., 0a1b2c3d4e). If not provided, a random one is generated.",
        min_length=10,
        max_length=10,
        pattern=r"^[0-9a-fA-F]{10}$",
        examples=["fedcba9876"],
    ),
    subnet_id: str = Query(
        "0001",
        title="Subnet ID",
        description="4-character hexadecimal Subnet ID (e.g., 0001).",
        min_length=4,
        max_length=4,
        pattern=r"^[0-9a-fA-F]{4}$",
        examples=["0001", "abcd"],
    ),
):
    """Generate an IPv6 Unique Local Address (ULA) based on RFC 4193."""
    try:
        # If Global ID is not provided, generate a random 40-bit one
        if not global_id:
            global_id_int = secrets.randbits(40)
            global_id_hex = format(global_id_int, "010x")
        else:
            global_id_hex = global_id.lower()
            global_id_int = int(global_id_hex, 16)

        # Get Subnet ID as integer
        subnet_id_hex = subnet_id.lower()
        subnet_id_int = int(subnet_id_hex, 16)

        # Construct the /48 ULA prefix
        # FC00::/7 prefix, L=1 (locally assigned)
        # FD00::/8 + 40-bit Global ID + 16-bit Subnet ID
        prefix_int = (0xFD << 56) | (global_id_int << 16) | subnet_id_int

        # Format the prefix as an IPv6 address string (first address in the /64)
        # We use the prefix as the network part and :: as the interface part
        ula_prefix_address = ipaddress.IPv6Address(prefix_int << 64)

        # Create the full /64 prefix string
        ula_prefix = f"{ula_prefix_address.exploded.split('::')[0]}::{subnet_id_hex}/64"
        # Note: A simpler way is just to construct the address string directly:
        ula_address_str = f"fd{global_id_hex[:2]}:{global_id_hex[2:6]}:{global_id_hex[6:]}:{subnet_id_hex}::1"

        return Ipv6UlaResponse(
            ula_address=ula_address_str,  # Example address within the prefix
            global_id=global_id_hex,
            subnet_id=subnet_id_hex,
        )

    except ValueError as ve:
        # Should be caught by Query regex, but good practice
        logger.warning(f"Invalid hex format for Global ID or Subnet ID: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid hex format: {str(ve)}",
        )
    except Exception as e:
        logger.error(f"Error generating IPv6 ULA: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate IPv6 ULA: {str(e)}",
        )
