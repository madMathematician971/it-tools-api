import logging
import re

from fastapi import APIRouter, HTTPException, status

from models.numeronym_models import NumeronymInput, NumeronymOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/numeronym", tags=["Numeronym Generator"])


def create_numeronym(word: str) -> str | None:
    "Creates a numeronym for a single word if it meets the length requirement."
    if len(word) < 3:  # Need at least first, last, and one char between
        return None
    # Calculate number of letters between first and last
    count = len(word) - 2
    return f"{word[0]}{count}{word[-1]}"


@router.post(
    "/",
    response_model=NumeronymOutput,
    summary="Generate numeronyms within text",
)
async def generate_numeronyms(input_data: NumeronymInput):
    """Convert text to numeronyms or decode numeronyms back to text."""
    try:
        text = input_data.text.strip()
        if not text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text cannot be empty")

        mode = input_data.mode.lower()

        if mode == "convert":
            # Split text into words and non-words (punctuation, spaces)
            # Regex finds sequences of word characters or sequences of non-word characters
            parts = re.findall(r"(\w+|[^\w]+)", text)

            result_parts = []
            for part in parts:
                if re.match(r"^\w+$", part):  # If it's a word
                    if len(part) >= 4:  # Use 4 as default minimum length
                        numeronym = create_numeronym(part)
                        if numeronym:
                            result_parts.append(numeronym)
                        else:
                            result_parts.append(part)
                    else:
                        result_parts.append(part)  # Word is too short
                else:
                    result_parts.append(part)  # Not a word, keep as is (space/punctuation)

            result = "".join(result_parts)
        elif mode == "decode":
            result = decode_numeronym(text)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid mode. Use 'convert' or 'decode'"
            )

        return NumeronymOutput(original=text, result=result, mode=mode)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing numeronym: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process numeronym: {str(e)}"
        )


def decode_numeronym(text: str) -> str:
    """Attempt to decode numeronyms, but can only make a best guess.

    This is an approximate decoding as the original word is not preserved.
    """
    result = []
    words = text.split()

    for word in words:
        # Check if this looks like a numeronym (first char + digits + last char)
        match = re.match(r"^([a-zA-Z])(\d+)([a-zA-Z])$", word)
        if match:
            first, number, last = match.groups()
            # Create placeholder word
            placeholder_len = int(number) + 2  # +2 for first and last chars
            # Use _ for missing middle characters
            placeholder = first + "_" * (placeholder_len - 2) + last
            result.append(placeholder)
        else:
            # Not a numeronym, keep as is
            result.append(word)

    return " ".join(result)
