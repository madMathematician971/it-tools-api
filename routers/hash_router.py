import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.hash_calculator import calculate_hash
from models.hash_models import HashInput, HashOutput

router = APIRouter(prefix="/api/hash", tags=["Hash"])

logger = logging.getLogger(__name__)


@router.post("/calculate", response_model=HashOutput)
async def calculate_hashes(payload: HashInput):
    """Calculate various hash digests for the input text."""
    try:
        return calculate_hash(payload.text)
    except Exception as e:
        logger.error(f"Error calculating hashes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during hash calculation",
        )
