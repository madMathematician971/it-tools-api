import html

from fastapi import APIRouter, HTTPException, status

from models.html_entities_models import HtmlEntitiesInput, HtmlEntitiesOutput

router = APIRouter(prefix="/api/html-entities", tags=["HTML Entities"])


@router.post("/encode", response_model=HtmlEntitiesOutput)
async def html_entities_encode(payload: HtmlEntitiesInput):
    """Encode special characters into HTML entities."""
    try:
        encoded_text = html.escape(payload.text, quote=True)  # quote=True also escapes "
        return {"result": encoded_text}
    except Exception as e:
        print(f"Error encoding HTML entities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during encoding",
        )


@router.post("/decode", response_model=HtmlEntitiesOutput)
async def html_entities_decode(payload: HtmlEntitiesInput):
    """Decode HTML entities back into characters."""
    try:
        decoded_text = html.unescape(payload.text)
        return {"result": decoded_text}
    except Exception as e:
        print(f"Error decoding HTML entities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during decoding",
        )
