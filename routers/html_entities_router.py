import logging

from fastapi import APIRouter, HTTPException, status

# Import tool functions
from mcp_server.tools.html_entities_processor import decode_html_entities, encode_html_entities
from models.html_entities_models import HtmlEntitiesInput, HtmlEntitiesOutput

router = APIRouter(prefix="/api/html-entities", tags=["HTML Entities"])
logger = logging.getLogger(__name__)


@router.post("/encode", response_model=HtmlEntitiesOutput)
async def html_entities_encode_endpoint(payload: HtmlEntitiesInput):
    """Encode special characters into HTML entities using the MCP tool."""
    try:
        result = encode_html_entities(text=payload.text)
        if error := result.get("error"):
            logger.warning(f"HTML entities encode tool failed: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error)

        encoded_text = result.get("result")
        if encoded_text is None:
            logger.error("Tool returned no error but also no result for encoding.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error: Tool failed to encode."
            )

        return {"result": encoded_text}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error encoding HTML entities: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.post("/decode", response_model=HtmlEntitiesOutput)
async def html_entities_decode_endpoint(payload: HtmlEntitiesInput):
    """Decode HTML entities back into characters using the MCP tool."""
    try:
        result = decode_html_entities(text=payload.text)
        if error := result.get("error"):
            logger.warning(f"HTML entities decode tool failed: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error)

        decoded_text = result.get("result")
        if decoded_text is None:
            logger.error("Tool returned no error but also no result for decoding.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error: Tool failed to decode."
            )

        return {"result": decoded_text}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error decoding HTML entities: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


# Removed original logic
