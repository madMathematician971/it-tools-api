"""MCP Tool for generating Lorem Ipsum placeholder text."""

import logging
from typing import Any

from lorem_text import lorem

from mcp_server import mcp_app

logger = logging.getLogger(__name__)

# Define constants for types to avoid magic strings
LOREM_TYPE_WORDS = "words"
LOREM_TYPE_SENTENCES = "sentences"
LOREM_TYPE_PARAGRAPHS = "paragraphs"


@mcp_app.tool()
def generate_lorem(lorem_type: str, count: int = 1) -> dict[str, Any]:
    """
    Generate Lorem Ipsum placeholder text.

    Args:
        lorem_type: The type of text to generate ('words', 'sentences', 'paragraphs').
        count: The number of words, sentences, or paragraphs to generate (default: 1).

    Returns:
        A dictionary containing:
            text: The generated Lorem Ipsum text.
            error: Error message if generation failed.
    """
    try:
        # Validate type and count
        if lorem_type not in [LOREM_TYPE_WORDS, LOREM_TYPE_SENTENCES, LOREM_TYPE_PARAGRAPHS]:
            valid_types = [LOREM_TYPE_WORDS, LOREM_TYPE_SENTENCES, LOREM_TYPE_PARAGRAPHS]
            return {"text": "", "error": f"Invalid lorem_type. Must be one of: {valid_types}"}

        if not isinstance(count, int) or count < 1:
            return {"text": "", "error": "Count must be a positive integer."}

        # Generate text based on type
        result_text = ""
        if lorem_type == LOREM_TYPE_WORDS:
            result_text = lorem.words(count)
        elif lorem_type == LOREM_TYPE_SENTENCES:
            # Ensure consistent spacing for multiple sentences
            sentences = [lorem.sentence() for _ in range(count)]
            result_text = " ".join(sentences)
        elif lorem_type == LOREM_TYPE_PARAGRAPHS:
            # Ensure consistent spacing for multiple paragraphs
            paragraphs = [lorem.paragraph() for _ in range(count)]
            result_text = "\n\n".join(paragraphs)

        return {"text": result_text, "error": None}

    except Exception as e:
        logger.error(f"Error generating Lorem Ipsum: {e}", exc_info=True)
        return {"text": "", "error": f"Internal server error during Lorem Ipsum generation: {str(e)}"}
