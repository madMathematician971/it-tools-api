import logging

from fastapi import APIRouter, HTTPException, status

# Import the tool function
from mcp_server.tools.iban_processor import validate_iban
from models.iban_models import IbanInput, IbanValidationOutput

router = APIRouter(prefix="/api/iban", tags=["IBAN"])
logger = logging.getLogger(__name__)


@router.post("/validate", response_model=IbanValidationOutput)
async def validate_iban_endpoint(payload: IbanInput):
    """Validate an IBAN string and parse its components using the MCP tool."""
    try:
        result = validate_iban(iban_string=payload.iban_string)

        # The tool handles validation logic and returns a structured response
        # We just need to check for unexpected internal errors from the tool itself.
        # Specific validation errors (like bad checksum) are part of the normal response.
        if error := result.get("error"):
            if "unexpected error" in error.lower():
                logger.error(f"IBAN tool encountered an internal error: {error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error during IBAN validation.",
                )

        # Ensure required fields are present even on validation failure (they should be None)
        if "is_valid" not in result:
            logger.error("IBAN tool returned response missing 'is_valid' field.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error: Tool response incomplete."
            )

        # Return the full result from the tool (includes error messages for invalid IBANs)
        return result

    except HTTPException as e:
        raise e  # Re-raise explicit HTTP exceptions
    except Exception as e:
        # Catch truly unexpected errors during endpoint execution
        logger.error(f"Unexpected error in IBAN validation endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )
