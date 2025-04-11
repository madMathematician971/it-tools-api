import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/unicode-converter", tags=["Unicode Converter"])


class UnicodeInput(BaseModel):
    text: str = Field(
        ...,
        description="Text to convert to Unicode code points or Unicode code points to convert back to text.",
    )
    prefix: str = Field(
        default="U+",
        description="Prefix for each Unicode code point (e.g., 'U+', '\\u'). Used for encoding.",
    )
    separator: str = Field(
        default=" ",
        description="Separator between encoded Unicode points. Used for encoding and decoding.",
    )
    base: int = Field(
        16,
        description="Numerical base for representing the code point (e.g., 16 for hex, 10 for decimal).",
        ge=2,
        le=36,
    )


class UnicodeOutput(BaseModel):
    result: str = Field(..., description="The resulting Unicode code point string or decoded text.")


# Helper to convert integer to specified base
def int_to_base(n, b):
    if n == 0:
        return "0"
    digits = []
    while n:
        digits.append(int(n % b))
        n //= b
    # Handling bases > 10 using ASCII
    return "".join(str(i) if i < 10 else chr(ord("A") + i - 10) for i in digits[::-1])


@router.post(
    "/encode",
    response_model=UnicodeOutput,
    summary="Convert text to Unicode code points",
)
async def text_to_unicode(payload: UnicodeInput):
    """Converts each character of the input text to its Unicode code point representation."""
    try:
        if not payload.text:
            return UnicodeOutput(result="")

        unicode_points = []
        for char in payload.text:
            code_point = ord(char)
            formatted_point = int_to_base(code_point, payload.base)
            # Add padding for hex if needed (common convention)
            if payload.base == 16:
                formatted_point = formatted_point.zfill(4)
            unicode_points.append(f"{payload.prefix}{formatted_point}")

        result = payload.separator.join(unicode_points)
        return UnicodeOutput(result=result)
    except Exception as e:
        logger.error(f"Error converting text to Unicode points: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during text-to-Unicode conversion: {str(e)}",
        )


@router.post(
    "/decode",
    response_model=UnicodeOutput,
    summary="Convert Unicode code points back to text",
)
async def unicode_to_text(payload: UnicodeInput):
    """Convert a string of Unicode code points back into text."""
    try:
        text = payload.text.strip()
        if not text:
            return UnicodeOutput(result="")

        code_points_str = []
        if payload.separator:
            # Split by separator if provided
            code_points_str = text.split(payload.separator)
        elif payload.prefix:
            # Handle concatenated codes if prefix is known and separator is empty
            current_pos = 0
            while current_pos < len(text):
                start_pos = text.find(payload.prefix, current_pos)
                if start_pos == -1:
                    break  # No more prefixes found
                code_start = start_pos + len(payload.prefix)
                next_prefix_pos = text.find(payload.prefix, code_start)
                if next_prefix_pos == -1:
                    code_points_str.append(text[start_pos:])  # Get the rest of the string
                    break
                else:
                    code_points_str.append(text[start_pos:next_prefix_pos])
                    current_pos = next_prefix_pos
        else:
            # No separator and no prefix - assume single code point? Or treat as error?
            # For now, assume single code point for backward compatibility/simplicity
            code_points_str = [text]

        decoded_chars = []
        for cp_str in code_points_str:
            if not cp_str:
                continue

            # Remove prefix if present
            processed_cp_str = cp_str
            if payload.prefix and cp_str.startswith(payload.prefix):
                processed_cp_str = cp_str[len(payload.prefix) :]
            elif payload.prefix:
                # If prefix is expected but not found, treat as error or skip?
                logger.debug(f"Expected prefix '{payload.prefix}' not found in '{cp_str}', skipping.")
                # Alternatively, raise error: raise HTTPException(...) or append '?'
                continue

            if not processed_cp_str:
                logger.debug(f"Empty code point string after removing prefix from '{cp_str}', skipping.")
                continue

            try:
                # Convert from specified base
                code_point_int = int(processed_cp_str, payload.base)
                decoded_chars.append(chr(code_point_int))
            except ValueError:
                logger.warning(f"Could not convert '{processed_cp_str}' from base {payload.base}. Original: '{cp_str}'")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid code point value '{processed_cp_str}' for base {payload.base}.",
                )
            except OverflowError:
                logger.warning(
                    f"Decoded integer {processed_cp_str} (base {payload.base}) is outside valid Unicode range."
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Code point value '{processed_cp_str}' is outside the valid Unicode range.",
                )

        result = "".join(decoded_chars)
        return UnicodeOutput(result=result)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error converting Unicode points to text: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during Unicode-to-text conversion: {str(e)}",
        )
