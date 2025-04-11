from fastapi import APIRouter, HTTPException, status
from jose import jwt

from models.jwt_models import JwtInput, JwtOutput

router = APIRouter(prefix="/api/jwt", tags=["JWT"])


@router.post("/parse", response_model=JwtOutput)
async def parse_jwt(payload: JwtInput):
    """Decode a JWT and optionally verify its signature."""
    token = payload.jwt_string
    secret = payload.secret_or_key
    algorithms = payload.algorithms

    try:
        # 1. Decode Header (Unverified)
        try:
            header = jwt.get_unverified_header(token)
        except Exception as e:
            return {"error": f"Failed to decode header: {e}"}  # Generic fallback

        # 2. Decode Payload (Unverified)
        try:
            unverified_payload = jwt.get_unverified_claims(token)
        except Exception as e:
            return {
                "header": header,
                "error": f"Failed to decode payload: {e}",
            }  # Generic fallback

        # 3. Verify Signature (Optional)
        signature_verified = None
        verification_error = None
        verified_payload = None

        if secret:
            try:
                # Determine required algorithms based on header or input
                alg = header.get("alg")
                required_algorithms = algorithms if algorithms else ([alg] if alg else None)
                if not required_algorithms:
                    raise Exception("Algorithm missing in header and not provided in input.")

                # Attempt verification
                verified_payload = jwt.decode(
                    token,
                    secret,
                    algorithms=required_algorithms,
                    # Add options like audience, issuer validation if needed
                    # options={"verify_aud": False, ...}
                )
                signature_verified = True
            except Exception as e:
                signature_verified = False
                verification_error = f"Error during verification process: {e}"

        # Determine final payload to return (verified if possible, else unverified)
        final_payload = verified_payload if signature_verified else unverified_payload

        output = {
            "header": header,
            "payload": final_payload,
            "signature_verified": signature_verified,
            "error": verification_error,  # Return verification error if verification was attempted
        }
        # Clean None values if preferred
        return {k: v for k, v in output.items() if v is not None}

    except Exception as e:
        print(f"Unexpected error parsing JWT: {e}")
        # This should ideally not be reached if specific errors are caught
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during JWT parsing",
        )
