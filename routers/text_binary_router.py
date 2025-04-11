import logging
from typing import Dict

from fastapi import APIRouter, HTTPException, status

from models.text_binary_models import TextBinaryInput, TextBinaryOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/text-binary", tags=["Text Binary Converter"])


@router.post("/", response_model=TextBinaryOutput)
async def convert_text_binary(input_data: TextBinaryInput):
    """Convert between text and binary representation."""
    # Store original text before stripping
    original_text = input_data.text
    try:
        mode = input_data.mode.lower()
        # Strip text for processing, but keep original for output
        text = original_text.strip()

        if not text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text cannot be empty")

        if mode == "text_to_binary":
            result, char_map = text_to_binary(
                original_text, include_spaces=input_data.include_spaces, space_replacement=input_data.space_replacement
            )
        elif mode == "binary_to_text":
            result, char_map = binary_to_text(original_text)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversion mode. Use 'text_to_binary' or 'binary_to_text'",
            )

        # Return original_text, not the stripped version
        return TextBinaryOutput(original=original_text, result=result, mode=mode, char_mapping=char_map)

    except HTTPException as http_exc:  # Re-raise specific HTTPExceptions
        raise http_exc
    except ValueError as ve:  # Convert expected ValueErrors to 400
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:  # Catch unexpected errors as 500
        logger.error(f"Error converting between text and binary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}"
        )


def text_to_binary(
    text: str, include_spaces: bool = True, space_replacement: str = "00100000"
) -> tuple[str, Dict[str, str]]:
    """Convert text to binary representation."""
    binary_values = []
    char_map = {}

    for char in text:
        # Get ASCII value then convert to binary, removing '0b' prefix
        binary = bin(ord(char))[2:].zfill(8)
        binary_values.append(binary)
        char_map[char] = binary

    # Join with or without spaces
    result = " ".join(binary_values) if include_spaces else "".join(binary_values)
    return result, char_map


def binary_to_text(binary: str) -> tuple[str, Dict[str, str]]:
    """Convert binary representation back to text."""
    # Remove any spaces in the binary string
    clean_binary = binary.replace(" ", "")

    # Check if the binary string is valid
    if not all(bit in "01" for bit in clean_binary):
        raise ValueError("Invalid binary input. Only 0s, 1s, and spaces are allowed")

    # Check if the length is a multiple of 8
    if len(clean_binary) % 8 != 0:
        raise ValueError(f"Binary length must be a multiple of 8. Current length: {len(clean_binary)}")

    # Convert 8-bit chunks to characters
    result = ""
    char_map = {}

    for i in range(0, len(clean_binary), 8):
        chunk = clean_binary[i : i + 8]
        try:
            char = chr(int(chunk, 2))
            result += char
            char_map[chunk] = char
        except ValueError:
            raise ValueError(f"Invalid binary chunk: {chunk}")

    return result, char_map
