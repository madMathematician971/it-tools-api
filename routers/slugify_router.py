from fastapi import APIRouter, HTTPException, status
from slugify import slugify  # Import python-slugify

from models.slugify_models import SlugifyInput, SlugifyOutput

router = APIRouter(prefix="/api/slugify", tags=["Slugify"])


@router.post("/create", response_model=SlugifyOutput)
async def create_slug(payload: SlugifyInput):
    """Convert a string into a URL-friendly slug."""
    try:
        # Basic slugify, options like separator, max_length can be added
        result_slug = slugify(payload.text)
        return {"slug": result_slug}
    except Exception as e:
        print(f"Error creating slug: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during slug creation",
        )
