"""Tool for expanding IPv4 CIDR blocks or hyphenated ranges into a list of IPs."""

import ipaddress
import logging
from typing import Any, List

logger = logging.getLogger(__name__)

# Arbitrary limit to prevent excessively large results
MAX_ADDRESSES_TO_RETURN = 65536


def expand_ipv4_range(ip_range: str) -> dict[str, Any]:
    """
    Expands an IPv4 CIDR block or hyphenated IP range into a list of individual IP addresses.

    The returned list of addresses is limited to MAX_ADDRESSES_TO_RETURN.

    Args:
        ip_range: The IPv4 range string (CIDR or hyphenated).

    Returns:
        A dictionary containing:
            count: Total number of addresses in the full range.
            addresses: List of individual IPv4 addresses (potentially truncated).
            truncated: Boolean indicating if the address list was truncated.
            error: An error message if parsing or expansion failed.
    """
    ip_input = ip_range.strip()
    if not ip_input:
        return {
            "count": 0,
            "addresses": [],
            "truncated": False,
            "error": "IP range input cannot be empty.",
        }

    addresses: List[str] = []
    total_count = 0
    truncated = False

    try:
        # Try parsing as CIDR
        if "/" in ip_input:
            try:
                network = ipaddress.ip_network(ip_input, strict=False)
                if not isinstance(network, ipaddress.IPv4Network):
                    # This case should ideally be caught by ip_network, but included for safety
                    raise ValueError("Input is not a valid IPv4 CIDR notation.")

                total_count = network.num_addresses
                logger.debug(f"CIDR: {ip_input} -> Total addresses: {total_count}")

                # Determine if truncation is needed and set the limit
                truncated = total_count > MAX_ADDRESSES_TO_RETURN
                limit = min(total_count, MAX_ADDRESSES_TO_RETURN)

                logger.debug(f"Limit: {limit}, Truncated: {truncated}")

                addresses = []
                # Use the network object's iterator which includes all addresses
                addr_iterator = iter(network)
                for _ in range(limit):
                    try:
                        # Get the next address from the iterator
                        addresses.append(str(next(addr_iterator)))
                    except StopIteration:
                        # This should not happen if limit <= total_count, but handles edge cases
                        logger.warning(f"StopIteration encountered unexpectedly for {ip_input} with limit {limit}")
                        break

            except ValueError as e:
                logger.info(f"Invalid CIDR format '{ip_input}': {e}")
                # Return specific error from ipaddress library
                return {
                    "count": 0,
                    "addresses": [],
                    "truncated": False,
                    "error": f"Invalid IPv4 CIDR notation: {str(e)}",
                }

        # Try parsing as hyphenated range
        elif "-" in ip_input:
            parts = ip_input.split("-")
            if len(parts) != 2:
                return {
                    "count": 0,
                    "addresses": [],
                    "truncated": False,
                    "error": "Invalid hyphenated range format. Use START_IP-END_IP.",
                }

            try:
                start_ip_str, end_ip_str = parts[0].strip(), parts[1].strip()
                start_ip = ipaddress.IPv4Address(start_ip_str)
                end_ip = ipaddress.IPv4Address(end_ip_str)

                if start_ip > end_ip:
                    return {
                        "count": 0,
                        "addresses": [],
                        "truncated": False,
                        "error": "Start IP address must be less than or equal to End IP address.",
                    }

                start_ip_int = int(start_ip)
                end_ip_int = int(end_ip)
                total_count = end_ip_int - start_ip_int + 1
                logger.debug(f"Hyphenated: {start_ip_str}-{end_ip_str} -> Total addresses: {total_count}")

                # Determine if truncation is needed and set the limit
                truncated = total_count > MAX_ADDRESSES_TO_RETURN
                limit = min(total_count, MAX_ADDRESSES_TO_RETURN)

                addresses = []
                generated_count = 0
                for i in range(limit):  # Generate exactly 'limit' addresses
                    addresses.append(str(ipaddress.IPv4Address(start_ip_int + i)))
                    generated_count = i + 1

            except ipaddress.AddressValueError as e:
                logger.info(f"Invalid IP address in range '{ip_input}': {e}")
                return {
                    "count": 0,
                    "addresses": [],
                    "truncated": False,
                    "error": f"Invalid IP address in range: {str(e)}",
                }
            except ValueError as e:
                logger.info(f"Invalid format within range '{ip_input}': {e}")
                return {
                    "count": 0,
                    "addresses": [],
                    "truncated": False,
                    "error": f"Invalid IP address format in range: {str(e)}",
                }

        # Try parsing as single IP
        else:
            try:
                ip_addr = ipaddress.IPv4Address(ip_input)
                # Treat single IP as a range of one
                total_count = 1
                addresses = [str(ip_addr)]
                truncated = False  # Single IP is never truncated
                limit = 1  # Only one address
                logger.debug(f"Single IP: {ip_input} -> Count: {total_count}")
            except ipaddress.AddressValueError:
                return {
                    "count": 0,
                    "addresses": [],
                    "truncated": False,
                    "error": "Invalid input format. Use CIDR (e.g., 1.2.3.0/24) or range (e.g., 1.2.3.4-1.2.3.10) or a single IP.",
                }

        return {"count": total_count, "addresses": addresses, "truncated": truncated, "error": None}

    except Exception as e:
        logger.error(f"Unexpected error expanding IPv4 range '{ip_input}': {e}", exc_info=True)
        return {
            "count": 0,
            "addresses": [],
            "truncated": False,
            "error": f"An unexpected error occurred during expansion: {str(e)}",
        }
