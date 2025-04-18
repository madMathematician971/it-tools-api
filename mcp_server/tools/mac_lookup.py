"""MCP Tool for looking up MAC address vendor information."""

import logging
from typing import Any

# Third-party library for lookup
from mac_vendor_lookup import InvalidMacError, MacLookup, VendorNotFoundError

from mcp_server import mcp_app

logger = logging.getLogger(__name__)


def _is_mac_local(normalized_mac_or_raw: str) -> bool | None:
    """Check if a MAC address is locally administered."""
    clean_mac = "".join(filter(str.isalnum, normalized_mac_or_raw)).upper()
    if len(clean_mac) < 2:
        return None
    try:
        first_byte = int(clean_mac[0:2], 16)
        return (first_byte & 0x02) != 0  # Check U/L bit
    except ValueError:
        return None


def _get_oui_from_mac(mac_address: str) -> str | None:
    """Extract the OUI (first 6 hex chars) from a MAC address string."""
    try:
        # Join all alphanumeric characters first
        alnum_chars = filter(str.isalnum, mac_address)
        clean_mac = "".join(alnum_chars).upper()

        # Check length *after* cleaning
        if len(clean_mac) < 6:
            return None  # Too short to have a full OUI

        oui_part = clean_mac[:6]

        # Validate that the OUI part contains *only* hex digits
        if all(c in "0123456789ABCDEF" for c in oui_part):
            return oui_part
        else:
            return None  # Invalid characters found in potential OUI part
    except Exception:
        return None


@mcp_app.tool()
async def lookup_mac_vendor(mac_address: str) -> dict[str, Any]:
    """
    Lookup vendor information for a given MAC address or OUI.

    Args:
        mac_address: The MAC address string (e.g., "00:1A:2B:3C:4D:5E", "001A2B3C4D5E").

    Returns:
        A dictionary containing:
            oui: The OUI part of the MAC address (string, 6 hex chars) or None.
            company: The vendor name (string) or None if not found.
            is_private: Whether the MAC is locally administered (boolean) or None if indeterminable.
            error: Error message if lookup failed.
    """
    # Determine OUI and private status based on input *before* potential library errors
    oui = _get_oui_from_mac(mac_address)
    is_private = _is_mac_local(mac_address)

    try:
        mac_lookup_client: MacLookup | None = None
        try:
            mac_lookup_client = MacLookup()
        except Exception as init_e:
            logger.error(f"Failed to initialize MacLookup client during request: {init_e}", exc_info=True)
            return {
                "oui": oui,
                "company": None,
                "is_private": is_private,
                "error": "MAC lookup service initialization failed.",
            }

        # Ensure async interface is available
        if not hasattr(mac_lookup_client, "async_lookup"):
            logger.warning("MacLookup async interface not found, falling back to sync.")
            vendor = mac_lookup_client.lookup(mac_address)
        else:
            vendor = await mac_lookup_client.async_lookup.lookup(mac_address)

        return {"oui": oui, "company": vendor, "is_private": is_private, "error": None}

    except VendorNotFoundError:
        logger.info(f"Vendor not found for MAC/OUI: {mac_address}")
        return {"oui": oui, "company": None, "is_private": is_private, "error": "Vendor not found for this OUI."}

    except InvalidMacError as e:
        logger.warning(f"Invalid MAC format detected by library for {mac_address}: {e}")
        return {"oui": oui, "company": None, "is_private": is_private, "error": f"Invalid MAC address format: {str(e)}"}

    except Exception as e:
        logger.error(f"Error during MAC lookup for {mac_address}: {e}", exc_info=True)
        return {
            "oui": oui,
            "company": None,
            "is_private": is_private,
            "error": f"Lookup failed due to an internal error: {str(e)}",
        }
