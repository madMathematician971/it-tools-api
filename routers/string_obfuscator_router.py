import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/string-obfuscator", tags=["String Obfuscator"])

# --- Full-Width Character Obfuscation Logic ---

# Mapping basic ASCII to full-width Unicode characters
# Starts from ASCII 33 (!) to 126 (~)
FULL_WIDTH_OFFSET = 0xFEE0
ASCII_START = 33
ASCII_END = 126
# Special case for space (ASCII 32)
FULL_WIDTH_SPACE = "\u3000"  # Ideographic Space


def obfuscate_to_full_width(text: str) -> str:
    "Converts specific ASCII characters (letters, numbers, basic punctuation, space) to full-width."
    obfuscated_chars = []
    for char in text:
        ascii_val = ord(char)
        if char == " ":
            obfuscated_chars.append(FULL_WIDTH_SPACE)
        # Check ranges for A-Z, a-z, 0-9
        elif (
            ord("A") <= ascii_val <= ord("Z") or ord("a") <= ascii_val <= ord("z") or ord("0") <= ascii_val <= ord("9")
        ):
            obfuscated_chars.append(chr(ascii_val + FULL_WIDTH_OFFSET))
        # Check specific punctuation within the ASCII range that has full-width forms
        elif ASCII_START <= ascii_val <= ASCII_END:
            # Map only specific punctuation that typically have full-width forms
            # Example: Convert ! " # $ % & ' ( ) * + , - . / : ; < = > ? @ [ \ ] ^ _ ` { | } ~
            # We map by offset, assuming direct correspondence for this range subset
            # Characters not explicitly having a direct map by offset might need a lookup table if required
            obfuscated_chars.append(chr(ascii_val + FULL_WIDTH_OFFSET))
        else:
            obfuscated_chars.append(char)  # Keep other chars (non-ASCII, control chars) as is
    return "".join(obfuscated_chars)


def deobfuscate_from_full_width(text: str) -> str:
    "Converts full-width Unicode characters back to their standard ASCII equivalents."
    deobfuscated_chars = []
    for char in text:
        if char == FULL_WIDTH_SPACE:
            deobfuscated_chars.append(" ")
        else:
            char_code = ord(char)
            # Calculate potential original ASCII value
            original_ascii_val = char_code - FULL_WIDTH_OFFSET
            # Check if the original value falls within the convertible ranges/chars
            if (
                (ord("A") <= original_ascii_val <= ord("Z"))
                or (ord("a") <= original_ascii_val <= ord("z"))
                or (ord("0") <= original_ascii_val <= ord("9"))
                or (ASCII_START <= original_ascii_val <= ASCII_END)
            ):  # Assuming punctuation was mapped directly
                deobfuscated_chars.append(chr(original_ascii_val))
            else:
                # Keep characters that aren't recognized full-width equivalents as is
                deobfuscated_chars.append(char)
    return "".join(deobfuscated_chars)


# --- API Models ---


class ObfuscatorInput(BaseModel):
    text: str = Field(..., description="The text to obfuscate or deobfuscate.")


class ObfuscatorOutput(BaseModel):
    result: str = Field(..., description="The resulting obfuscated or deobfuscated text.")


# --- API Endpoints ---


@router.post(
    "/obfuscate/full-width",
    response_model=ObfuscatorOutput,
    summary="Obfuscate text using full-width Unicode characters",
)
async def obfuscate_string(payload: ObfuscatorInput):
    """Converts standard ASCII characters (space, !, ", ..., ~) to their full-width Unicode equivalents."""
    try:
        result = obfuscate_to_full_width(payload.text)
        return ObfuscatorOutput(result=result)
    except Exception as e:
        logger.error(f"Error obfuscating string: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during string obfuscation: {str(e)}",
        )


@router.post(
    "/deobfuscate/full-width",
    response_model=ObfuscatorOutput,
    summary="Deobfuscate text from full-width Unicode characters",
)
async def deobfuscate_string(payload: ObfuscatorInput):
    """Converts full-width Unicode characters back to their standard ASCII equivalents."""
    try:
        result = deobfuscate_from_full_width(payload.text)
        return ObfuscatorOutput(result=result)
    except Exception as e:
        logger.error(f"Error deobfuscating string: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during string deobfuscation: {str(e)}",
        )
