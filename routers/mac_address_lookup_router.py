import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status

# Import the library
from mac_vendor_lookup import InvalidMacError, MacLookup, VendorNotFoundError

from models.mac_address_lookup_models import MacLookupInput, MacLookupOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the client once
try:
    # The sync client provides access to the async one
    mac_lookup_client = MacLookup()
except Exception as e:
    logger.error(f"Failed to initialize MacLookup client: {e}")
    mac_lookup_client = None

router = APIRouter(prefix="/api/mac-address-lookup", tags=["MAC Address Lookup"])


def is_mac_local(normalized_mac_or_raw: str) -> Optional[bool]:
    """Check if a MAC address (potentially unnormalized) is locally administered."""
    # Attempt basic normalization for check
    clean_mac = "".join(filter(str.isalnum, normalized_mac_or_raw)).upper()
    if len(clean_mac) < 2:
        return None  # Cannot determine
    try:
        first_byte = int(clean_mac[0:2], 16)
        return (first_byte & 0x02) != 0
    except ValueError:
        return None  # Invalid hex


def get_oui_from_mac(mac_address: str) -> Optional[str]:
    """Extract the OUI part from a MAC address string."""
    clean_mac = "".join(filter(str.isalnum, mac_address)).upper()
    if len(clean_mac) >= 6:
        return clean_mac[:6]
    return None


@router.post("/", response_model=MacLookupOutput)
async def lookup_mac_address(input_data: MacLookupInput):
    """Lookup vendor information for a given MAC address or OUI."""
    if not mac_lookup_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MAC lookup service is not available."
        )

    raw_input_mac = input_data.mac_address
    # Basic format is checked by Pydantic model

    # Pre-calculate OUI and is_private based on raw input for error reporting
    oui = get_oui_from_mac(raw_input_mac)
    is_private = is_mac_local(raw_input_mac)

    try:
        # Use the ASYNC lookup method and await it
        # Ensure the async client is available
        if not hasattr(mac_lookup_client, "async_lookup"):
            logger.error("Async lookup interface not available on mac_lookup_client.")
            raise Exception("MAC Lookup async client unavailable.")

        vendor = await mac_lookup_client.async_lookup.lookup(raw_input_mac)

        # If lookup succeeded, OUI and is_private status are reliable
        return MacLookupOutput(oui=oui, company=vendor, is_private=is_private)

    except VendorNotFoundError:
        logger.info(f"Vendor not found for MAC: {raw_input_mac}")
        # Still return oui and is_private status
        return MacLookupOutput(oui=oui, company=None, is_private=is_private, error="Vendor not found for this OUI.")

    except InvalidMacError as e:
        # This error comes from the library if internal validation fails
        logger.warning(f"Invalid MAC format detected by library for {raw_input_mac}: {e}")
        return MacLookupOutput(
            oui=oui, company=None, is_private=is_private, error=f"Invalid MAC address format: {str(e)}"
        )

    except ValueError as ve:
        # Raised by the Pydantic validator for basic format check
        return MacLookupOutput(oui=None, company=None, is_private=None, error=f"Invalid input format: {str(ve)}")

    except Exception as e:
        logger.error(f"Error looking up MAC address {raw_input_mac}: {e}", exc_info=True)
        return MacLookupOutput(
            oui=oui, company=None, is_private=is_private, error=f"Lookup failed due to an internal error."
        )
