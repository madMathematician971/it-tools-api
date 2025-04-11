import ipaddress
import logging

from fastapi import APIRouter

from models.ipv4_subnet_models import Ipv4SubnetInput, Ipv4SubnetOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Make sure router prefix is correct if it was changed accidentally
router = APIRouter(prefix="/api/ipv4/subnet-calculator", tags=["IPv4 Subnet Calculator"])


@router.post("/", response_model=Ipv4SubnetOutput)
async def calculate_ipv4_subnet(input_data: Ipv4SubnetInput):
    """Calculates subnet details for a given IPv4 address and CIDR prefix or netmask."""
    try:
        ip_cidr = input_data.ip_cidr.strip()
        if not ip_cidr:
            return Ipv4SubnetOutput(error="Invalid input format: Input cannot be empty.")

        try:
            network = ipaddress.ip_network(ip_cidr, strict=False)
        except ValueError as e:
            error_msg = f"Invalid input format: {str(e)}"
            logger.info(error_msg)
            return Ipv4SubnetOutput(error=error_msg)

        if not isinstance(network, ipaddress.IPv4Network):
            return Ipv4SubnetOutput(error="Input does not represent an IPv4 network.")

        # Additional check: If ipaddress parsed as /32, ensure input didn't contain '/'
        # This catches cases like "192.168.1.1/" which ipaddress might accept but are invalid user input.
        if network.prefixlen == 32 and "/" in ip_cidr and not ip_cidr.endswith("/32"):
            # Check if it looks like a mask was intended but invalid, ipaddress.ip_network might have defaulted to /32
            parts = ip_cidr.split("/")
            if len(parts) == 2 and parts[1] != "32":  # e.g. "192.168.1.1/" or "192.168.1.1/invalid"
                error_msg = "Invalid CIDR prefix or netmask provided after /."
                logger.info(f"{error_msg} Input: {ip_cidr}")
                return Ipv4SubnetOutput(error=error_msg)
            # If just a single IP was given, ipaddress correctly treats it as /32, which is fine.

        # Calculate details
        num_addresses = network.num_addresses
        num_hosts = num_addresses - 2 if num_addresses >= 2 else 0
        first_host = str(network.network_address + 1) if num_hosts > 0 else None
        last_host = str(network.broadcast_address - 1) if num_hosts > 0 else None

        # Determine IP type based on the *input* address, not the network address
        ip_part = ip_cidr.split("/")[0]
        try:
            input_ip = ipaddress.ip_address(ip_part)
        except ValueError:
            # If IP part itself is invalid (e.g., 'abc/24'), use network address for properties
            # This might happen if ip_network() succeeded due to a valid mask/prefix
            input_ip = network.network_address

        # Use network properties for boolean flags
        return Ipv4SubnetOutput(
            network_address=str(network.network_address),
            broadcast_address=str(network.broadcast_address),
            netmask=str(network.netmask),
            cidr_prefix=network.prefixlen,
            num_addresses=num_addresses,
            num_usable_hosts=num_hosts,
            first_usable_host=first_host,
            last_usable_host=last_host,
            is_private=network.is_private,
            is_multicast=network.is_multicast,
            is_loopback=network.is_loopback,
            error=None,
        )

    except Exception as e:
        logger.error(f"Error calculating subnet: {e}", exc_info=True)
        return Ipv4SubnetOutput(error=f"An unexpected error occurred: {str(e)}")
