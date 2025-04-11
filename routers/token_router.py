import secrets  # Use secrets for cryptographically secure random choices
import string

from fastapi import APIRouter, HTTPException, status

from models.token_models import CharSetType, TokenInput, TokenOutput

router = APIRouter(prefix="/api/token", tags=["Token Generator"])

CHARSET_MAP = {
    CharSetType.alphanumeric: string.ascii_letters + string.digits,
    CharSetType.alpha: string.ascii_letters,
    CharSetType.numeric: string.digits,
    CharSetType.hex_lower: string.digits + string.ascii_lowercase[:6],
    CharSetType.hex_upper: string.digits + string.ascii_uppercase[:6],
}


@router.post("/generate", response_model=TokenOutput)
async def generate_tokens(payload: TokenInput):
    """Generate random tokens with specified length, count, and character set."""
    charset = CHARSET_MAP.get(payload.charset_type)
    if not charset:
        # Should be caught by Pydantic, but as a fallback
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid charset_type specified.",
        )

    try:
        tokens = ["".join(secrets.choice(charset) for _ in range(payload.length)) for _ in range(payload.count)]
        return TokenOutput(tokens=tokens)
    except Exception as e:
        print(f"Error generating tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token generation",
        )
