import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.hmac_calculator import calculate_hmac
from models.hmac_models import HmacInput, HmacOutput

router = APIRouter(prefix="/api/hmac", tags=["HMAC"])

logger = logging.getLogger(__name__)


@router.post("/calculate", response_model=HmacOutput)
async def calculate_hmac_endpoint(payload: HmacInput):
    """Calculate HMAC digest for the input text using a secret key and hash algorithm."""
    try:
        return calculate_hmac(text=payload.text, key=payload.key, algorithm=payload.algorithm)
    except ValueError as e:
        logger.warning(f"HMAC calculation failed due to invalid input: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error calculating HMAC: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during HMAC calculation",
        )
