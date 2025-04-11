import bcrypt
from fastapi import APIRouter, HTTPException, status

from models.bcrypt_models import (
    BcryptHashInput,
    BcryptHashOutput,
    BcryptVerifyInput,
    BcryptVerifyOutput,
)

router = APIRouter(prefix="/api/bcrypt", tags=["bcrypt"])


@router.post("/hash", response_model=BcryptHashOutput)
async def bcrypt_hash(payload: BcryptHashInput):
    """Hash a password using bcrypt."""
    try:
        hashed_bytes = bcrypt.hashpw(payload.password.encode("utf-8"), bcrypt.gensalt(rounds=payload.salt_rounds))
        return {"hash": hashed_bytes.decode("utf-8")}
    except Exception as e:
        print(f"Error hashing password with bcrypt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during hashing",
        )


@router.post("/verify", response_model=BcryptVerifyOutput)
async def bcrypt_verify(payload: BcryptVerifyInput):
    """Verify a password against a bcrypt hash."""
    try:
        match = bcrypt.checkpw(payload.password.encode("utf-8"), payload.hash.encode("utf-8"))
        return {"match": match}
    except ValueError as e:
        print(f"Error verifying password with bcrypt (bad hash?): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid hash format provided.",
        )
    except Exception as e:
        print(f"Error verifying password with bcrypt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during verification",
        )
