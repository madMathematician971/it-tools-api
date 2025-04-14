"""
IPv4 subnet calculator tool for MCP server.
"""

import ipaddress
import logging
from typing import Any

from mcp_server import mcp_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@mcp_app.tool()
def calculate_ipv4_subnet(ip_cidr: str) -> dict[str, Any]:
    """
    Calculates IPv4 subnet details given an IP address and CIDR prefix or netmask.

    Args:
        ip_cidr: The IP address and CIDR/mask (e.g., "192.168.1.50/24").

    Returns:
        A dictionary containing calculated subnet details or an error message:
            network_address: Network address of the subnet
            broadcast_address: Broadcast address of the subnet
            netmask: Subnet mask
            cidr_prefix: CIDR prefix length
            num_addresses: Total number of IP addresses in the subnet
            num_usable_hosts: Number of usable host addresses
            first_usable_host: First usable host IP
            last_usable_host: Last usable host IP
            is_private: Whether the network is private
            is_multicast: Whether the network is multicast
            is_loopback: Whether the network is loopback
            error: Error message if calculation failed
    """
    # Default result structure with None values
    result = {
        "network_address": None,
        "broadcast_address": None,
        "netmask": None,
        "cidr_prefix": None,
        "num_addresses": None,
        "num_usable_hosts": None,
        "first_usable_host": None,
        "last_usable_host": None,
        "is_private": None,
        "is_multicast": None,
        "is_loopback": None,
        "error": None,
    }

    try:
        ip_cidr = ip_cidr.strip()
        if not ip_cidr:
            result["error"] = "Invalid input format: Input cannot be empty."
            return result

        try:
            # Use strict=False to allow host bits to be set (common input format)
            network = ipaddress.ip_network(ip_cidr, strict=False)
        except ValueError as e:
            error_msg = f"Invalid input format: {str(e)}"
            logger.info(error_msg)
            result["error"] = error_msg
            return result

        if not isinstance(network, ipaddress.IPv4Network):
            result["error"] = "Input does not represent an IPv4 network."
            return result

        # Handle edge cases where ipaddress might parse ambiguously
        if network.prefixlen == 32 and "/" in ip_cidr and not ip_cidr.endswith("/32"):
            parts = ip_cidr.split("/")
            if len(parts) == 2 and parts[1] != "32":
                error_msg = "Invalid CIDR prefix or netmask provided after /."
                logger.info(f"{error_msg} Input: {ip_cidr}")
                result["error"] = error_msg
                return result

        # Calculate details
        num_addresses = network.num_addresses
        num_hosts = num_addresses - 2 if num_addresses >= 2 else 0
        first_host = str(network.network_address + 1) if num_hosts > 0 else None
        last_host = str(network.broadcast_address - 1) if num_hosts > 0 else None

        # Update result with calculated values
        result.update(
            {
                "network_address": str(network.network_address),
                "broadcast_address": str(network.broadcast_address),
                "netmask": str(network.netmask),
                "cidr_prefix": network.prefixlen,
                "num_addresses": num_addresses,
                "num_usable_hosts": num_hosts,
                "first_usable_host": first_host,
                "last_usable_host": last_host,
                "is_private": network.is_private,
                "is_multicast": network.is_multicast,
                "is_loopback": network.is_loopback,
            }
        )

        return result

    except Exception as e:
        logger.error(f"Error calculating subnet for '{ip_cidr}': {e}", exc_info=True)
        result["error"] = f"An unexpected error occurred: {str(e)}"
        return result
