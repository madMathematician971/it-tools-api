import logging

from fastapi import APIRouter, HTTPException

from mcp_server.tools.ipv4_range_expander import expand_ipv4_range
from models.ipv4_range_expander_models import IPv4RangeInput, IPv4RangeOutput

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/expand-ipv4-range", response_model=IPv4RangeOutput)
async def expand_ipv4_range_endpoint(payload: IPv4RangeInput):
    """
    Expands an IPv4 range provided in CIDR or hyphenated format into a list of individual IP addresses.
    Optionally truncates the list to prevent excessively large responses.
    """
    logger.info(f"Received request to expand IPv4 range: {payload.range_input}, truncate: {payload.truncate}")

    try:
        result = expand_ipv4_range(payload.range_input)

        if result.get("error"):
            logger.warning(f"Error expanding IPv4 range '{payload.range_input}': {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])

        logger.info(
            f"Successfully expanded range '{payload.range_input}'. Count: {result['count']}, Truncated: {result['truncated']}"
        )
        return IPv4RangeOutput(count=result["count"], addresses=result["addresses"], truncated=result["truncated"])
    except HTTPException as e:
        # Re-raise HTTPExceptions directly
        raise e
    except Exception as e:
        logger.exception(f"Unexpected error expanding IPv4 range '{payload.range_input}': {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the IPv4 range.")
