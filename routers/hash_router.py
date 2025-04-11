import hashlib

from fastapi import APIRouter, HTTPException, status

from models.hash_models import HashInput, HashOutput

router = APIRouter(prefix="/api/hash", tags=["Hash"])


@router.post("/calculate", response_model=HashOutput)
async def calculate_hashes(payload: HashInput):
    """Calculate various hash digests for the input text."""
    try:
        text_bytes = payload.text.encode("utf-8")

        md5_hash = hashlib.md5(text_bytes).hexdigest()
        sha1_hash = hashlib.sha1(text_bytes).hexdigest()
        sha256_hash = hashlib.sha256(text_bytes).hexdigest()
        sha512_hash = hashlib.sha512(text_bytes).hexdigest()

        return {
            "md5": md5_hash,
            "sha1": sha1_hash,
            "sha256": sha256_hash,
            "sha512": sha512_hash,
        }
    except Exception as e:
        print(f"Error calculating hashes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during hash calculation",
        )
