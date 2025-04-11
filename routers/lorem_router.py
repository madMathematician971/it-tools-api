from fastapi import APIRouter, HTTPException, status
from lorem_text import lorem  # Import lorem-text

from models.lorem_models import LoremInput, LoremOutput, LoremType

router = APIRouter(prefix="/api/lorem", tags=["Lorem Ipsum"])


@router.post("/generate", response_model=LoremOutput)
async def generate_lorem(payload: LoremInput):
    """Generate Lorem Ipsum placeholder text."""
    try:
        if payload.lorem_type == LoremType.words:
            # Generate count words, s=1 ensures single block
            result_text = lorem.words(payload.count)
        elif payload.lorem_type == LoremType.sentences:
            # Call sentence() count times and join
            sentences = [lorem.sentence() for _ in range(payload.count)]
            result_text = " ".join(sentences)
        elif payload.lorem_type == LoremType.paragraphs:
            # Call paragraph() count times and join
            paragraphs = [lorem.paragraph() for _ in range(payload.count)]
            result_text = "\n\n".join(paragraphs)
        else:
            # Should be caught by Pydantic validation, but as a fallback
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid lorem_type specified.",
            )

        return {"text": result_text}
    except Exception as e:
        print(f"Error generating Lorem Ipsum: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during Lorem Ipsum generation",
        )
