"""
Phone number parsing tool for MCP server.
"""

import logging
from typing import Any

from phonenumbers import (
    NumberParseException,
    PhoneNumberFormat,
    PhoneNumberType,
    format_number,
    is_possible_number,
    is_valid_number,
    number_type,
    parse,
)

from mcp_server import mcp_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@mcp_app.tool()
def parse_phone_number(phone_number_string: str, default_country: str | None = None) -> dict[str, Any]:
    """
    Parse, validate, and format a phone number using the phonenumbers library.

    Args:
        phone_number_string: The phone number to parse.
        default_country: Optional default country code (e.g., US, GB).

    Returns:
        A dictionary containing:
            is_valid: Whether the number is valid
            parsed_number: Raw parsed object string representation
            country_code: Country code (e.g., 1 for US)
            national_number: National number portion
            extension: Any extension in the number
            number_type: Type of number (mobile, fixed line, etc.)
            e164_format: E.164 format (+14155552671)
            national_format: National format (415-555-2671)
            international_format: International format (+1 415-555-2671)
            error: Error message if parsing failed
    """
    try:
        # Parse the number, providing default country if available
        parsed = parse(phone_number_string, default_country)

        # Basic possibility check
        is_possible = is_possible_number(parsed)
        # Strict validity check (length, prefix for the region)
        is_valid = is_valid_number(parsed)

        if not is_possible and not is_valid:  # If not even possible, definitely not valid
            return {"is_valid": False, "error": "Number is not possible.", "parsed_number": str(parsed)}

        # If possible but not strictly valid, return specific error
        if not is_valid:
            return {
                "is_valid": False,
                "error": "Number is possible but not valid (e.g., incorrect length/format for region).",
                "parsed_number": str(parsed),
            }

        # Format in different ways (only if valid)
        e164 = format_number(parsed, PhoneNumberFormat.E164)
        national = format_number(parsed, PhoneNumberFormat.NATIONAL)
        international = format_number(parsed, PhoneNumberFormat.INTERNATIONAL)

        # Extract components
        country_code = parsed.country_code
        national_num = str(parsed.national_number)
        ext = parsed.extension or None  # Ensure None if empty

        # Get number type description
        type_code = number_type(parsed)
        type_map = {
            PhoneNumberType.FIXED_LINE: "Fixed line",
            PhoneNumberType.MOBILE: "Mobile",
            PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed line or mobile",
            PhoneNumberType.TOLL_FREE: "Toll-free",
            PhoneNumberType.PREMIUM_RATE: "Premium rate",
            PhoneNumberType.SHARED_COST: "Shared cost",
            PhoneNumberType.VOIP: "VoIP",
            PhoneNumberType.PERSONAL_NUMBER: "Personal number",
            PhoneNumberType.PAGER: "Pager",
            PhoneNumberType.UAN: "UAN (User Assigned Number)",
            PhoneNumberType.VOICEMAIL: "Voicemail",
            PhoneNumberType.UNKNOWN: "Unknown",
        }
        number_type_desc = type_map.get(type_code, "Unknown")

        return {
            "is_valid": True,
            "parsed_number": str(parsed),
            "country_code": country_code,
            "national_number": national_num,
            "extension": ext,
            "number_type": number_type_desc,
            "e164_format": e164,
            "national_format": national,
            "international_format": international,
            "error": None,
        }

    except NumberParseException as e:
        # Error during initial parsing
        return {"is_valid": False, "error": f"Parsing failed: {e}"}
    except Exception as e:
        logger.error(f"Error processing phone number '{phone_number_string}': {e}", exc_info=True)
        # Return a generic error for the tool
        return {"is_valid": False, "error": f"Internal server error during processing: {str(e)}"}
