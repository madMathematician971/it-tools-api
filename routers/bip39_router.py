import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.bip39_generator import generate_bip39_mnemonic
from models.bip39_models import Bip39Input, Bip39Output

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bip39", tags=["BIP39"])


@router.post("/generate", response_model=Bip39Output)
async def bip39_generate_endpoint(payload: Bip39Input):
    """Generate a BIP39 mnemonic seed phrase using the tool."""
    try:
        result = generate_bip39_mnemonic(word_count=payload.word_count, language=payload.language)

        if result["error"]:
            # Check for specific known user errors first
            if "Invalid word_count" in result["error"]:
                logger.warning(f"Invalid word_count provided: {payload.word_count}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result["error"],
                )
            # Log other tool errors and return a generic 500
            logger.error(f"BIP39 tool returned an unexpected error: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during mnemonic generation",
            )

        # Tool executed successfully
        return Bip39Output(
            mnemonic=result["mnemonic"],
            word_count=result["word_count"],
            language=result["language"],  # Return the canonical language used
        )

    except HTTPException as http_exc:  # Re-raise HTTPException for specific error handling above
        raise http_exc
    except Exception as e:
        # Catch any unexpected exceptions during the tool call or processing
        logger.error(f"Unexpected error in /bip39/generate endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected internal server error",
        )
