import hashlib
import hmac

from fastapi import APIRouter, HTTPException, status

from models.hmac_models import HmacInput, HmacOutput

router = APIRouter(prefix="/api/hmac", tags=["HMAC"])

# Map algorithm names to hashlib functions
HASH_ALGOS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
    # Add others if needed (sha224, sha384, etc.)
}


@router.post("/calculate", response_model=HmacOutput)
async def calculate_hmac(payload: HmacInput):
    """Calculate HMAC digest for the input text using a secret key and hash algorithm."""
    algo_name = payload.algorithm.lower()
    if algo_name not in HASH_ALGOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported algorithm. Supported: {list(HASH_ALGOS.keys())}",
        )

    try:
        text_bytes = payload.text.encode("utf-8")
        key_bytes = payload.key.encode("utf-8")
        hash_func = HASH_ALGOS[algo_name]

        hmac_digest = hmac.new(key_bytes, text_bytes, hash_func).hexdigest()

        return {"hmac_hex": hmac_digest}
    except Exception as e:
        print(f"Error calculating HMAC: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during HMAC calculation",
        )
