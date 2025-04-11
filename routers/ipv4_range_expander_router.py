import ipaddress
import logging
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ipv4-range-expander", tags=["IPv4 Range Expander"])

# Arbitrary limit to prevent excessively large requests
MAX_ADDRESSES_TO_RETURN = 65536  # Corresponds to a /16, adjust as needed


class Ipv4RangeInput(BaseModel):
    ip_range: str = Field(
        ...,
        description="IPv4 range in CIDR notation (e.g., 192.168.1.0/24) or hyphenated range (e.g., 192.168.1.10-192.168.1.20).",
    )


class Ipv4RangeOutput(BaseModel):
    count: int = Field(..., description="Total number of addresses in the expanded range.")
    addresses: List[str] = Field(
        ...,
        description=f"List of individual IPv4 addresses (limited to {MAX_ADDRESSES_TO_RETURN}).",
    )
    truncated: bool = Field(
        ...,
        description="Indicates if the returned address list was truncated due to size limits.",
    )


@router.post(
    "/expand",
    response_model=Ipv4RangeOutput,
    summary="Expand IPv4 CIDR or range to list individual IPs",
)
async def expand_ipv4_range(payload: Ipv4RangeInput):
    """Expands an IPv4 CIDR block or hyphenated IP range into a list of individual IP addresses."""
    ip_input = payload.ip_range.strip()
    if not ip_input:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="IP range input cannot be empty.",
        )

    try:
        addresses = []
        total_count = 0
        truncated = False

        # Try parsing as CIDR
        if "/" in ip_input:
            try:
                network = ipaddress.ip_network(ip_input, strict=False)  # strict=False allows host bits set
                if not isinstance(network, ipaddress.IPv4Network):
                    raise ValueError("Input is not a valid IPv4 CIDR.")  # Should be caught below, but safer
                total_count = network.num_addresses
                if total_count > MAX_ADDRESSES_TO_RETURN:
                    truncated = True
                    # Iterate only up to the limit
                    for i, ip in enumerate(network):
                        if i >= MAX_ADDRESSES_TO_RETURN:
                            break
                        addresses.append(str(ip))
                else:
                    addresses = [str(ip) for ip in network]
            except ValueError as e:
                logger.info(f"Invalid CIDR format '{ip_input}': {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid IPv4 CIDR notation: '{ip_input}'. {str(e)}",
                )

        # Try parsing as hyphenated range
        elif "-" in ip_input:
            parts = ip_input.split("-")
            if len(parts) != 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid hyphenated range format. Use START_IP-END_IP.",
                )

            try:
                start_ip_str, end_ip_str = parts[0].strip(), parts[1].strip()
                start_ip = ipaddress.IPv4Address(start_ip_str)
                end_ip = ipaddress.IPv4Address(end_ip_str)

                if start_ip > end_ip:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Start IP address must be less than or equal to End IP address.",
                    )

                total_count = int(end_ip) - int(start_ip) + 1
                current_ip_int = int(start_ip)
                end_ip_int = int(end_ip)

                if total_count > MAX_ADDRESSES_TO_RETURN:
                    truncated = True
                    limit = MAX_ADDRESSES_TO_RETURN
                else:
                    limit = total_count

                for i in range(limit):
                    addresses.append(str(ipaddress.IPv4Address(current_ip_int + i)))

            except ipaddress.AddressValueError as e:
                logger.info(f"Invalid IP address in range '{ip_input}': {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid IP address in range: '{ip_input}'. {str(e)}",
                )
            except ValueError as e:  # Catch potential issues if split parts aren't valid IPs
                logger.info(f"Invalid IP address format within range '{ip_input}': {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid IP address format in range: '{ip_input}'. Ensure both parts are valid IPv4 addresses. {str(e)}",
                )

        else:
            # If neither CIDR nor range, it might be a single IP - treat as /32 CIDR
            try:
                ip_addr = ipaddress.IPv4Address(ip_input)
                network = ipaddress.ip_network(f"{ip_addr}/32")
                total_count = 1
                addresses = [str(ip_addr)]
            except ipaddress.AddressValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input format. Use CIDR (e.g., 1.2.3.0/24) or range (e.g., 1.2.3.4-1.2.3.10).",
                )

        return Ipv4RangeOutput(count=total_count, addresses=addresses, truncated=truncated)

    except HTTPException as http_exc:
        raise http_exc  # Re-raise validation errors
    except Exception as e:
        logger.error(f"Error expanding IPv4 range '{payload.ip_range}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during IPv4 range expansion: {str(e)}",
        )
