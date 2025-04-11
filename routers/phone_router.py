from fastapi import APIRouter, HTTPException, status
from phonenumbers import NumberParseException, PhoneNumberFormat, format_number, is_valid_number, parse

from models.phone_models import PhoneInput, PhoneOutput

router = APIRouter(prefix="/api/phone", tags=["Phone Number"])


@router.post("/parse", response_model=PhoneOutput)
async def parse_phone_number(payload: PhoneInput):
    """Parse and format a phone number."""
    try:
        # Parse the number
        # Pass default_country (e.g., 'US') if number might be national
        parsed = parse(payload.phone_number_string, payload.default_country)

        # Check validity
        is_valid = is_valid_number(parsed)
        if not is_valid:
            # It might be parseable but not valid (e.g., wrong length for country)
            return {
                "is_valid": False,
                "error": "Number is not valid.",
                "parsed_number": str(parsed),
            }

        # Format in different ways
        e164 = format_number(parsed, PhoneNumberFormat.E164)
        national = format_number(parsed, PhoneNumberFormat.NATIONAL)
        international = format_number(parsed, PhoneNumberFormat.INTERNATIONAL)

        # Extract components
        country_code = parsed.country_code
        national_num = str(parsed.national_number)
        ext = parsed.extension
        cc_source = str(parsed.country_code_source)

        return {
            "is_valid": True,
            "parsed_number": str(parsed),  # Raw parsed object string representation
            "country_code": country_code,
            "national_number": national_num,
            "extension": ext,
            "country_code_source": cc_source,
            "e164_format": e164,
            "national_format": national,
            "international_format": international,
            "error": None,
        }

    except NumberParseException as e:
        # Error during initial parsing
        return {"is_valid": False, "error": f"Parsing failed: {e}"}
    except Exception as e:
        print(f"Error processing phone number: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during phone number processing",
        )
