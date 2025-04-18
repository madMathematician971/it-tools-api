import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

# Import tool function
from mcp_server.tools.ipv6_ula_generator import generate_ipv6_ula as generate_ipv6_ula_tool
from models.ipv6_ula_models import Ipv6UlaResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ipv6-ula", tags=["IPv6 ULA Generator"])


@router.get("/", response_model=Ipv6UlaResponse)
async def generate_ipv6_ula_endpoint(
    global_id: Optional[str] = Query(
        None,
        title="Global ID",
        description="Optional 10-character hexadecimal Global ID (e.g., 0a1b2c3d4e). If not provided, a random one is generated.",
        min_length=10,
        max_length=10,
        pattern=r"^[0-9a-fA-F]{10}$",
        examples=["fedcba9876"],
    ),
    subnet_id: str = Query(
        "0001",
        title="Subnet ID",
        description="4-character hexadecimal Subnet ID (e.g., 0001).",
        min_length=4,
        max_length=4,
        pattern=r"^[0-9a-fA-F]{4}$",
        examples=["0001", "abcd"],
    ),
):
    """Generate an IPv6 Unique Local Address (ULA) based on RFC 4193."""
    try:
        # Call the tool function
        result_dict = generate_ipv6_ula_tool(
            global_id=global_id,
            subnet_id=subnet_id,
        )

        # Check for errors returned by the tool
        if result_dict.get("error"):
            logger.info(f"IPv6 ULA generation failed: {result_dict['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result_dict["error"],
            )

        # Return the successful result from the tool
        # The tool's return dict matches the Ipv6UlaResponse model
        return result_dict

    except HTTPException:  # Re-raise HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Error generating IPv6 ULA: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate IPv6 ULA: {str(e)}",
        )
