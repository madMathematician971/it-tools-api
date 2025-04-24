"""
NATO Phonetic Alphabet Converter tool for MCP server.
"""

import logging
import re
from typing import Any

from mcp_server import mcp_app

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

# Create reverse mapping for decoding (handle case insensitivity)
NATO_REVERSE = {v.lower(): k for k, v in NATO_ALPHABET.items()}
NATO_REVERSE["xray"] = "X"  # Add common variation
# Add symbols explicitly to ensure they are mapped correctly
NATO_REVERSE["space"] = " "
NATO_REVERSE["period"] = "."
NATO_REVERSE["comma"] = ","
NATO_REVERSE["question mark"] = "?"
NATO_REVERSE["exclamation mark"] = "!"
NATO_REVERSE["dash"] = "-"
NATO_REVERSE["underscore"] = "_"
NATO_REVERSE["at sign"] = "@"
NATO_REVERSE["hash"] = "#"
NATO_REVERSE["dollar"] = "$"
NATO_REVERSE["percent"] = "%"
NATO_REVERSE["ampersand"] = "&"
NATO_REVERSE["asterisk"] = "*"
NATO_REVERSE["plus"] = "+"
NATO_REVERSE["equals"] = "="
NATO_REVERSE["slash"] = "/"
NATO_REVERSE["backslash"] = "\\"
NATO_REVERSE["left parenthesis"] = "("
NATO_REVERSE["right parenthesis"] = ")"
NATO_REVERSE["left bracket"] = "["
NATO_REVERSE["right bracket"] = "]"
NATO_REVERSE["left brace"] = "{"
NATO_REVERSE["right brace"] = "}"
NATO_REVERSE["less than"] = "<"
NATO_REVERSE["greater than"] = ">"
NATO_REVERSE["colon"] = ":"
NATO_REVERSE["semicolon"] = ";"
NATO_REVERSE["double quote"] = '"'
NATO_REVERSE["single quote"] = "'"
NATO_REVERSE["backtick"] = "`"
NATO_REVERSE["vertical bar"] = "|"
NATO_REVERSE["tilde"] = "~"
NATO_REVERSE["caret"] = "^"


@mcp_app.tool()
def convert_to_nato(
    text: str,
    output_format: str = "text",
    separator: str = " ",
    include_original: bool = True,
    lowercase: bool = False,
) -> dict[str, Any]:
    """
    Convert text to NATO phonetic alphabet representation.

    Args:
        text: Text to convert
        output_format: Output format (list, text)
        separator: Separator for text format output
        include_original: Include original character in output
        lowercase: Convert result to lowercase

    Returns:
        A dictionary containing:
            result: Dictionary with 'output' (string or list of strings) and 'character_map'
            error: Optional error message
    """
    try:
        if not text:
            return {"result": None, "error": "Input text cannot be empty"}

        char_map = {}
        nato_text_parts = []

        for char in text:
            upper_char = char.upper()
            # If char is a digit, use the digit itself, otherwise lookup or use Unknown
            if char.isdigit():
                nato_word = char
                char_map[char] = char  # Map digit to itself
            else:
                nato_word = NATO_ALPHABET.get(upper_char, f"Unknown ({char})")
                char_map[char] = NATO_ALPHABET.get(upper_char, f"Unknown ({char})")  # Original mapping for non-digits

            if lowercase and not char.isdigit():  # Don't lowercase digits
                nato_word = nato_word.lower()

            # Handle space character separately when including original
            if include_original:
                if char == " ":
                    nato_entry = nato_word  # Just the word "Space" (or "space")
                elif char.isdigit():
                    nato_entry = char  # Just the digit itself
                else:
                    nato_entry = f"{nato_word}"
            else:
                nato_entry = nato_word

            nato_text_parts.append(nato_entry)

        if output_format.lower() == "list":
            output = nato_text_parts
        else:
            output = separator.join(nato_text_parts)

        result_data = {"output": output, "character_map": char_map}
        return {"result": result_data, "error": None}

    except Exception as e:
        logger.error(f"Error converting to NATO alphabet: {e}", exc_info=True)
        return {"result": None, "error": f"Failed to convert to NATO alphabet: {str(e)}"}


@mcp_app.tool()
def convert_from_nato(nato_text: str, separator: str = " ") -> dict[str, Any]:
    """
    Converts a string of NATO phonetic words back to text.

    Args:
        nato_text: String of NATO words
        separator: Separator used between NATO words

    Returns:
        A dictionary containing:
            result: Decoded text string
            error: Optional error message
    """
    try:
        if not nato_text:
            return {"result": "", "error": None}

        # Return error if separator is empty
        if separator == "":
            return {"result": None, "error": "Empty separator is not allowed for decoding."}

        # Build a sorted list of NATO words/phrases, longest first, for matching
        # Ensure lowercase for case-insensitive matching
        sorted_nato_keys = sorted(NATO_REVERSE.keys(), key=len, reverse=True)

        # Prepare the text for processing: normalize spaces around the separator
        # and strip leading/trailing whitespace.
        normalized_text = nato_text.strip().lower()
        # Split carefully, handling multiple spaces around separator
        pattern = rf"\s*{re.escape(separator)}\s*"
        nato_words = [word for word in re.split(pattern, normalized_text) if word]

        decoded_chars = []
        i = 0
        while i < len(nato_words):
            matched = False
            current_word = nato_words[i]

            # Check if the current word is a digit first
            if current_word.isdigit():
                decoded_chars.append(current_word)
                i += 1
                matched = True
            else:
                # If not a digit, try matching longest phrases in NATO_REVERSE
                for length in range(min(3, len(nato_words) - i), 0, -1):
                    phrase = " ".join(nato_words[i : i + length])
                    if phrase in NATO_REVERSE:
                        decoded_chars.append(NATO_REVERSE[phrase])
                        i += length
                        matched = True
                        break  # Found longest match

            if not matched:
                # If it wasn't a digit and no phrase matched, treat as unknown
                decoded_chars.append("?")
                i += 1

        result = "".join(decoded_chars)
        return {"result": result, "error": None}

    except Exception as e:
        logger.error(f"Error converting NATO alphabet to text: {e}", exc_info=True)
        return {"result": None, "error": f"Internal server error during NATO-to-text conversion: {str(e)}"}
