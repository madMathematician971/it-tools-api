import logging

from fastapi import APIRouter, HTTPException, status

# Import the existing tool
from mcp_server.tools.bip39_generator import generate_bip39_mnemonic as generate_bip39_mnemonic_tool
from models.bip39_models import Bip39Input, Bip39Output

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bip39", tags=["BIP39 Mnemonic Generator"])


@router.post("/generate", response_model=Bip39Output)
async def generate_mnemonic_endpoint(payload: Bip39Input):
    """Generate a BIP39 mnemonic seed phrase using the MCP tool."""

    # Call the existing MCP tool
    result = generate_bip39_mnemonic_tool(word_count=payload.word_count, language=payload.language)

    if result.get("error"):
        error_detail = result["error"]
        logger.warning(f"BIP39 tool returned error: {error_detail}")
        # The tool already validates word_count, so this should be a 400
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)

    # Map canonical language back if needed for output, though unlikely needed
    # as output model expects string
    output_language = result.get("language", payload.language)  # Fallback to input lang

    return Bip39Output(
        mnemonic=result["mnemonic"],
        word_count=result["word_count"],
        language=output_language,  # Return the language used (likely canonical)
    )
