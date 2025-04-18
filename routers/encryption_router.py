import logging

from fastapi import APIRouter, HTTPException, status

# Import the tool functions
from mcp_server.tools.encryption_processor import decrypt_text, encrypt_text
from models.encryption_models import CryptoDecryptInput, CryptoDecryptOutput, CryptoEncryptOutput, CryptoInput

router = APIRouter(prefix="/api/crypto", tags=["Encryption"])

logger = logging.getLogger(__name__)


@router.post("/encrypt", response_model=CryptoEncryptOutput)
async def crypto_encrypt_endpoint(payload: CryptoInput):
    """Encrypt text using the MCP encryption tool."""
    try:
        result = encrypt_text(text=payload.text, password=payload.password, algorithm=payload.algorithm)

        if error := result.get("error"):
            logger.warning(f"Encryption tool failed: {error}")
            if "Unsupported algorithm" in error or "cannot be encoded" in error:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid input: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Tool error: {error}")

        ciphertext = result.get("ciphertext")
        if ciphertext is None:
            logger.error("Tool returned no error but also no ciphertext.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal error: Tool failed to produce ciphertext.",
            )

        return {"ciphertext": ciphertext}

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during encryption endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.post("/decrypt", response_model=CryptoDecryptOutput)
async def crypto_decrypt_endpoint(payload: CryptoDecryptInput):
    """Decrypt text using the MCP encryption tool."""
    try:
        result = decrypt_text(ciphertext=payload.ciphertext, password=payload.password, algorithm=payload.algorithm)

        if error := result.get("error"):
            logger.warning(f"Decryption tool failed: {error}")
            if (
                "Unsupported algorithm" in error
                or "Invalid Base64" in error
                or "Ciphertext is too short" in error
                or "Decryption failed" in error
                or "not valid UTF-8" in error
            ):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Decryption failed: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Tool error: {error}")

        plaintext = result.get("plaintext")
        if plaintext is None:
            logger.error("Tool returned no error but also no plaintext.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal error: Tool failed to produce plaintext.",
            )

        return {"plaintext": plaintext}

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during decryption endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )
