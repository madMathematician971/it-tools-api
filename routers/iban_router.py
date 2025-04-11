from fastapi import (
    APIRouter,
)
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

from models.iban_models import IbanInput, IbanValidationOutput

router = APIRouter(prefix="/api/iban", tags=["IBAN"])


@router.post("/validate", response_model=IbanValidationOutput)
async def validate_iban(payload: IbanInput):
    """Validate an IBAN string and parse its components."""
    try:
        iban = IBAN(payload.iban_string)
        # If no exception is raised, it's structurally valid
        return {
            "is_valid": True,
            "iban_string_formatted": iban.formatted,  # Formatted with spaces
            "country_code": iban.country_code,
            "check_digits": iban.checksum_digits,
            "bban": iban.bban,
            # Add other parsed components if desired
            # "bank_code": iban.bank_code,
            # "account_code": iban.account_code,
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
    ) as e:
        # Specific validation errors
        return {"is_valid": False, "error": str(e)}
    except SchwiftyException as e:
        # Catch other schwifty-specific errors
        return {"is_valid": False, "error": f"Validation error: {str(e)}"}
    except Exception as e:
        # Other unexpected errors
        print(f"Error validating IBAN: {e}")
        # Don't raise 500, just report as invalid with generic error
        return {"is_valid": False, "error": f"An unexpected error occurred: {e}"}
        # Or raise 500:
        # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during IBAN validation")
