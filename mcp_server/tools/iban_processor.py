"""Tool for validating and parsing IBAN strings using the schwifty library."""

import logging
from typing import Any

from schwifty import IBAN
from schwifty.exceptions import (
    InvalidAccountCode,
    InvalidBankCode,
    InvalidBBANChecksum,
    InvalidBranchCode,
    InvalidChecksumDigits,
    InvalidCountryCode,
    InvalidLength,
    InvalidStructure,
    SchwiftyException,
)

logger = logging.getLogger(__name__)


def validate_iban(iban_string: str) -> dict[str, Any]:
    """
    Validate an IBAN string and parse its components using the schwifty library.

    Args:
        iban_string: The IBAN string to validate.

    Returns:
        A dictionary containing:
            is_valid: Boolean indicating if the IBAN is valid.
            iban_string_formatted: Formatted IBAN with spaces (if valid).
            country_code: Two-letter country code (if valid).
            check_digits: Check digits (if valid).
            bban: Basic Bank Account Number (if valid).
            error: An error message string if validation failed, otherwise None.
    """
    try:
        iban = IBAN(iban_string)
        # If no exception is raised, it's structurally valid and passes checksums
        return {
            "is_valid": True,
            "iban_string_formatted": iban.formatted,  # Formatted with spaces
            "country_code": iban.country_code,
            "check_digits": iban.checksum_digits,
            "bban": iban.bban,
            "error": None,
        }
    except (
        InvalidStructure,
        InvalidChecksumDigits,
        InvalidLength,
        InvalidCountryCode,
        InvalidBBANChecksum,
        InvalidAccountCode,
        InvalidBankCode,
        InvalidBranchCode,
        SchwiftyException,  # Catch specific schwifty errors
    ) as e:
        # Specific validation errors
        logger.info(f"IBAN validation failed for '{iban_string}': {e}")
        return {
            "is_valid": False,
            "iban_string_formatted": None,
            "country_code": None,
            "check_digits": None,
            "bban": None,
            "error": str(e),
        }
    except Exception as e:
        # Other unexpected errors
        logger.error(f"Unexpected error validating IBAN '{iban_string}': {e}", exc_info=True)
        return {
            "is_valid": False,
            "iban_string_formatted": None,
            "country_code": None,
            "check_digits": None,
            "bban": None,
            "error": f"An unexpected error occurred during validation: {str(e)}",
        }
