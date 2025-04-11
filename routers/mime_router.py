import mimetypes

from fastapi import APIRouter, HTTPException, status

from models.mime_models import (
    MimeExtensionLookupInput,
    MimeExtensionLookupOutput,
    MimeTypeLookupInput,
    MimeTypeLookupOutput,
)

router = APIRouter(prefix="/api/mime", tags=["MIME Types"])

# Ensure mimetypes database is initialized
mimetypes.init()


@router.post("/lookup-type", response_model=MimeTypeLookupOutput)
async def lookup_mime_type(payload: MimeTypeLookupInput):
    """Look up the MIME type for a given file extension."""
    # Ensure extension starts with a dot for guess_type
    ext = payload.extension if payload.extension.startswith(".") else "." + payload.extension
    try:
        mime_type, encoding = mimetypes.guess_type(f"filename{ext}", strict=False)
        return {"mime_type": mime_type, "extension": payload.extension}
    except Exception as e:
        print(f"Error looking up MIME type: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during MIME type lookup",
        )


@router.post("/lookup-extension", response_model=MimeExtensionLookupOutput)
async def lookup_mime_extension(payload: MimeExtensionLookupInput):
    """Look up common file extensions for a given MIME type."""
    mime_type = payload.mime_type.lower().strip()
    try:
        extensions = mimetypes.guess_all_extensions(mime_type, strict=False)
        return {"extensions": extensions, "mime_type": mime_type}
    except Exception as e:
        print(f"Error looking up MIME extensions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during extension lookup",
        )
