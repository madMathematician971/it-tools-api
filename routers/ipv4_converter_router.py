import logging

from fastapi import APIRouter, HTTPException, status

# Import the tool function
from mcp_server.tools.ipv4_converter import convert_ipv4
from models.ipv4_converter_models import IPv4Input, IPv4Output

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ipv4-converter", tags=["IPv4 Address Converter"])


@router.post("/", response_model=IPv4Output)
async def convert_ipv4_endpoint(input_data: IPv4Input):
    """Convert IPv4 addresses between different formats using the MCP tool."""
    try:
        result = convert_ipv4(ip_address=input_data.ip_address, format_hint=input_data.format)

        # Check for tool errors
        if error := result.get("error"):
            logger.warning(f"IPv4 conversion tool failed for '{input_data.ip_address}': {error}")
            # Treat specific format/value errors as Bad Request
            if (
                "Invalid IP address format" in error
                or "Could not determine" in error
                or "cannot be empty" in error
                or "Unknown format hint" in error
            ):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
            # Assume other errors are internal
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Tool error: {error}")

        # Check for missing fields on success (should not happen)
        if not all(k in result for k in ["original", "dotted_decimal", "decimal", "hexadecimal", "binary"]):
            logger.error("IPv4 tool succeeded but returned incomplete data.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal error: Tool failed to provide complete results.",
            )

        # Return the successful result directly from the tool
        return result

    except HTTPException as e:
        raise e  # Re-raise explicit HTTP exceptions
    except Exception as e:
        logger.error(f"Error converting IPv4 address: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to convert IPv4 address: {str(e)}"
        )
