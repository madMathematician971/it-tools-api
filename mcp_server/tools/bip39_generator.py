"""
BIP39 mnemonic seed phrase generation tool for MCP server.
"""

import logging

from mnemonic import Mnemonic

from mcp_server import mcp_app

logger = logging.getLogger(__name__)

# Map short codes to canonical names used by the mnemonic library
LANGUAGE_MAP = {
    "en": "english",
    "es": "spanish",
    "fr": "french",
    "it": "italian",
    "jp": "japanese",
    "ko": "korean",
    "zh_hans": "chinese_simplified",
    "zh_hant": "chinese_traditional",
}
DEFAULT_LANGUAGE_CANONICAL = "english"

# Map word count to required entropy bits
SUPPORTED_WORD_COUNTS = {12: 128, 15: 160, 18: 192, 21: 224, 24: 256}


@mcp_app.tool()
def generate_bip39_mnemonic(word_count: int, language: str = "en") -> dict:
    """
    Generate a BIP39 mnemonic seed phrase.

    Args:
        word_count: Number of words in the mnemonic (12, 15, 18, 21, 24).
        language: Language code (e.g., 'en', 'es', 'fr', 'it', 'jp', 'ko', 'zh_hans', 'zh_hant'). Defaults to 'en'.

    Returns:
        A dictionary containing:
            mnemonic: The generated mnemonic phrase (string).
            word_count: The requested word count (int).
            language: The canonical language name used (string).
            error: An error message string if generation failed, otherwise None.
    """
    if word_count not in SUPPORTED_WORD_COUNTS:
        error_msg = f"Invalid word_count: {word_count}. Must be one of {list(SUPPORTED_WORD_COUNTS.keys())}."
        logger.warning(error_msg)
        return {"mnemonic": "", "word_count": word_count, "language": language, "error": error_msg}

    # Determine the canonical language name to use, default to English if not found
    language_canonical = LANGUAGE_MAP.get(language.lower(), DEFAULT_LANGUAGE_CANONICAL)

    try:
        # Instantiate Mnemonic with the canonical language name
        mnemo = Mnemonic(language_canonical)
    except ValueError:
        # This might happen if the language code is valid but library support is missing somehow
        # Fallback to English and log a warning
        logger.warning(f"Could not instantiate Mnemonic for language '{language_canonical}', falling back to English.")
        language_canonical = DEFAULT_LANGUAGE_CANONICAL
        try:
            mnemo = Mnemonic(language_canonical)
        except Exception as e:
            # If even English fails, log and return error
            error_msg = f"Failed to instantiate Mnemonic even for English: {e}"
            logger.error(error_msg, exc_info=True)
            return {"mnemonic": "", "word_count": word_count, "language": language_canonical, "error": error_msg}

    try:
        entropy_bits = SUPPORTED_WORD_COUNTS[word_count]
        mnemonic_phrase = mnemo.generate(strength=entropy_bits)
        logger.info(f"Generated {word_count}-word BIP39 mnemonic in {language_canonical}.")
        return {
            "mnemonic": mnemonic_phrase,
            "word_count": word_count,
            "language": language_canonical,
            "error": None,
        }
    except Exception as e:
        error_msg = f"Error generating BIP39 mnemonic: {e}"
        logger.error(error_msg, exc_info=True)
        return {"mnemonic": "", "word_count": word_count, "language": language_canonical, "error": error_msg}
