import logging
from urllib.parse import quote, unquote

from fastapi import APIRouter, HTTPException, status

from models.url_encoder_models import UrlEncoderInput, UrlEncoderOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/url-encoder", tags=["URL Encoder"])


@router.post("/", response_model=UrlEncoderOutput)
async def process_url_encoding(input_data: UrlEncoderInput):
    """Encode or decode URLs and URL components."""
    try:
        text = input_data.text.strip()
        if not text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text cannot be empty")

        mode = input_data.mode.lower()

        if mode == "encode":
            result = quote(text, safe="")
        elif mode == "decode":
            try:
                # Specify encoding and error handling for robustness
                result = unquote(text, encoding="utf-8", errors="replace")
            except Exception as decode_err:
                # Log the specific error for better debugging
                logger.warning(f"Failed to decode URL component '{text}': {decode_err}")
                return UrlEncoderOutput(
                    original=text, result="", mode=mode, error=f"Failed to decode URL: {str(decode_err)}"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid mode. Use 'encode' or 'decode'"
            )

        return UrlEncoderOutput(original=text, result=result, mode=mode)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing URL encoding: {e}", exc_info=True)
        return UrlEncoderOutput(
            original=input_data.text, result="", mode=input_data.mode, error=f"Error during processing: {str(e)}"
        )
