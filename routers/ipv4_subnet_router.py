import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.ipv4_subnet_calculator import calculate_ipv4_subnet
from models.ipv4_subnet_models import Ipv4SubnetInput, Ipv4SubnetOutput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ipv4/subnet-calculator", tags=["IPv4 Subnet Calculator"])


@router.post("/", response_model=Ipv4SubnetOutput)
async def calculate_ipv4_subnet_endpoint(input_data: Ipv4SubnetInput):
    """Calculates subnet details for a given IPv4 address and CIDR prefix or netmask."""
    try:
        # Call the tool function
        result = calculate_ipv4_subnet(input_data.ip_cidr)

        # Check if the tool returned an error
        if result.get("error"):
            logger.info(f"Subnet calculation failed for input '{input_data.ip_cidr}': {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        # Return the successful result from the tool
        # The Ipv4SubnetOutput model should match the dict structure
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in subnet endpoint for input '{input_data.ip_cidr}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}"
        )
