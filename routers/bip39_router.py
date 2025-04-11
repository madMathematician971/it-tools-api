from fastapi import APIRouter, HTTPException, status
from mnemonic import Mnemonic

from models.bip39_models import Bip39Input, Bip39Output

router = APIRouter(prefix="/api/bip39", tags=["BIP39"])

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


@router.post("/generate", response_model=Bip39Output)
async def bip39_generate(payload: Bip39Input):
    """Generate a BIP39 mnemonic seed phrase."""
    supported_word_counts = {12: 128, 15: 160, 18: 192, 21: 224, 24: 256}
    if payload.word_count not in supported_word_counts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid word_count. Must be one of {list(supported_word_counts.keys())}",
        )

    # Determine the canonical language name to use
    language_canonical = LANGUAGE_MAP.get(payload.language.lower(), DEFAULT_LANGUAGE_CANONICAL)

    # Instantiate Mnemonic with the canonical language name
    try:
        mnemo = Mnemonic(language_canonical)
    except ValueError:
        # Should not happen if LANGUAGE_MAP is correct, but as a fallback
        language_canonical = DEFAULT_LANGUAGE_CANONICAL
        mnemo = Mnemonic(language_canonical)

    try:
        entropy_bits = supported_word_counts[payload.word_count]
        # Use mnemonic library's generate method
        mnemonic_phrase = mnemo.generate(strength=entropy_bits)
        return {
            "mnemonic": mnemonic_phrase,
            "word_count": payload.word_count,
            # Return the language actually used for generation (canonical name)
            "language": language_canonical,
        }
    except Exception as e:
        print(f"Error generating BIP39 mnemonic: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error generating mnemonic",
        )
