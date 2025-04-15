import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.phone_parser import parse_phone_number as parse_phone_number_tool
from models.phone_models import PhoneInput, PhoneOutput

router = APIRouter(prefix="/api/phone", tags=["Phone Number"])
logger = logging.getLogger(__name__)


@router.post("/parse", response_model=PhoneOutput)
async def parse_phone_number_endpoint(payload: PhoneInput):
    """Parse and format a phone number."""
    try:
        # Call the tool function
        result_dict = parse_phone_number_tool(
            phone_number_string=payload.phone_number_string, default_country=payload.default_country
        )

        # Check for errors returned by the tool
        if result_dict.get("error"):
            logger.info(f"Phone number parsing failed: {result_dict['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result_dict["error"],
            )

        # Return successful result
        # The tool result dict should match the PhoneOutput model fields.
        return result_dict

    except HTTPException:  # Re-raise
        raise
    except Exception as e:
        logger.error(f"Error processing phone number: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during phone number processing",
        )
