import logging
import re

from fastapi import APIRouter, HTTPException, status

from models.nato_alphabet_models import NatoInput, NatoOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NATO phonetic alphabet mapping
NATO_ALPHABET = {
    "A": "Alpha",
    "B": "Bravo",
    "C": "Charlie",
    "D": "Delta",
    "E": "Echo",
    "F": "Foxtrot",
    "G": "Golf",
    "H": "Hotel",
    "I": "India",
    "J": "Juliet",
    "K": "Kilo",
    "L": "Lima",
    "M": "Mike",
    "N": "November",
    "O": "Oscar",
    "P": "Papa",
    "Q": "Quebec",
    "R": "Romeo",
    "S": "Sierra",
    "T": "Tango",
    "U": "Uniform",
    "V": "Victor",
    "W": "Whiskey",
    "X": "X-ray",
    "Y": "Yankee",
    "Z": "Zulu",
    "0": "Zero",
    "1": "One",
    "2": "Two",
    "3": "Three",
    "4": "Four",
    "5": "Five",
    "6": "Six",
    "7": "Seven",
    "8": "Eight",
    "9": "Nine",
    " ": "Space",
    ".": "Period",
    ",": "Comma",
    "?": "Question Mark",
    "!": "Exclamation Mark",
    "-": "Dash",
    "_": "Underscore",
    "@": "At Sign",
    "#": "Hash",
    "$": "Dollar",
    "%": "Percent",
    "&": "Ampersand",
    "*": "Asterisk",
    "+": "Plus",
    "=": "Equals",
    "/": "Slash",
    "\\": "Backslash",
    "(": "Left Parenthesis",
    ")": "Right Parenthesis",
    "[": "Left Bracket",
    "]": "Right Bracket",
    "{": "Left Brace",
    "}": "Right Brace",
    "<": "Less Than",
    ">": "Greater Than",
    ":": "Colon",
    ";": "Semicolon",
    '"': "Double Quote",
    "'": "Single Quote",
    "`": "Backtick",
    "|": "Vertical Bar",
    "~": "Tilde",
    "^": "Caret",
}

router = APIRouter(prefix="/api/nato-alphabet", tags=["NATO Phonetic Alphabet"])

# Create reverse mapping for decoding (handle case insensitivity)
NATO_REVERSE = {v.lower(): k for k, v in NATO_ALPHABET.items()}
# Add variations if needed, e.g., "Xray" might be common input
NATO_REVERSE["xray"] = "X"  # Example variation


@router.post("/", response_model=NatoOutput)
async def convert_to_nato(input_data: NatoInput):
    """Convert text to NATO phonetic alphabet representation."""
    try:
        if not input_data.text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text cannot be empty")

        # Map each character to its NATO equivalent
        char_map = {}
        nato_text_parts = []

        for char in input_data.text:
            upper_char = char.upper()
            nato_word = NATO_ALPHABET.get(upper_char, f"Unknown ({char})")

            # Store in character map
            char_map[char] = nato_word

            # Format for output
            if input_data.lowercase:
                nato_word = nato_word.lower()

            nato_entry = f"{char} - {nato_word}" if input_data.include_original else nato_word
            nato_text_parts.append(nato_entry)

        # Format the output based on the requested format
        if input_data.format.lower() == "table":
            output = "\n".join(nato_text_parts)
        elif input_data.format.lower() == "list":
            output = "• " + "\n• ".join(nato_text_parts)
        else:  # text format
            output = input_data.separator.join(nato_text_parts)

        return NatoOutput(
            input=input_data.text, output=output, format=input_data.format.lower(), character_map=char_map
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error converting to NATO alphabet: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to convert to NATO alphabet: {str(e)}"
        )


@router.post(
    "/decode",
    response_model=NatoOutput,
    summary="Convert NATO phonetic alphabet back to text",
)
async def nato_to_text(payload: NatoInput):
    """Converts a string of NATO phonetic words (separated by a separator) back to text."""
    try:
        if not payload.text:
            return NatoOutput(result="")

        separator = payload.separator if payload.separator else " "
        # Use regex to split while preserving separators within parentheses like (space)
        # This regex splits by the separator, but not if it's inside parentheses
        # It also handles cases where the separator might be multiple spaces
        nato_words = re.split(rf"{re.escape(separator)}+(?![^\(]*\))", payload.text.strip())

        decoded_chars = []
        for word in nato_words:
            if not word:
                continue
            # Lookup in lowercase reverse dict
            decoded_chars.append(NATO_REVERSE.get(word.lower(), "?"))  # Use ? for unknown words

        result = "".join(decoded_chars)
        return NatoOutput(result=result)

    except Exception as e:
        logger.error(f"Error converting NATO alphabet to text: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during NATO-to-text conversion: {str(e)}",
        )
