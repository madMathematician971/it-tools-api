import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.roman_numeral_converter import decode_from_roman as decode_from_roman_tool
from mcp_server.tools.roman_numeral_converter import encode_to_roman as encode_to_roman_tool
from models.roman_numeral_models import RomanDecodeInput, RomanEncodeInput, RomanOutput

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/roman-numerals", tags=["Roman Numeral Converter"])


@router.post("/encode", response_model=RomanOutput)
async def encode_to_roman_endpoint(input_data: RomanEncodeInput):
    """Convert an integer (1-3999) to its Roman numeral representation."""
    try:
        # Call the tool function
        result_dict = encode_to_roman_tool(number=input_data.number)

        # Check for errors from the tool
        if result_dict.get("error"):
            logger.info(f"Roman numeral encoding failed: {result_dict['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result_dict["error"],
            )

        # Return successful result
        # Tool result dict matches RomanOutput model
        return result_dict

    except HTTPException:  # Re-raise
        raise
    except Exception as e:
        logger.error(f"Error encoding to Roman numeral: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during encoding: {str(e)}"
        )


@router.post("/decode", response_model=RomanOutput)
async def decode_from_roman_endpoint(input_data: RomanDecodeInput):
    """Convert a Roman numeral string to its integer representation."""
    try:
        # Call the tool function
        result_dict = decode_from_roman_tool(roman_numeral=input_data.roman_numeral)

        # Check for errors from the tool
        # Note: The tool returns a warning in the 'error' field for non-standard forms,
        # but still provides the result. We might choose to return 200 OK with the warning.
        # For now, treat any non-None 'error' as a 400 Bad Request for consistency.
        if result_dict.get("error"):
            # If it's just a non-standard warning, maybe log it differently?
            log_level = logging.INFO if "Warning:" in result_dict["error"] else logging.WARNING
            logger.log(log_level, f"Roman numeral decoding failed/warned: {result_dict['error']}")
            # Decide if non-standard forms should be 400 or 200 with warning.
            # Let's stick to 400 for any error/warning for now.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result_dict["error"],
            )

        # Return successful result
        # Tool result dict matches RomanOutput model
        return result_dict

    # Keep general exception handler
    except HTTPException:  # Re-raise
        raise
    except Exception as e:
        logger.error(f"Error decoding Roman numeral: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during decoding: {str(e)}"
        )
