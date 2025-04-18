"""MCP Tool for parsing and optionally verifying JSON Web Tokens (JWTs)."""

import logging
from typing import Any

from jose import jwt

from mcp_server import mcp_app

logger = logging.getLogger(__name__)


@mcp_app.tool()
def parse_jwt(
    jwt_string: str,
    secret_or_key: str | None = None,
    algorithms: list[str] | None = None,
) -> dict[str, Any]:
    """
    Parse a JWT, decode header/payload, and optionally verify the signature.

    Args:
        jwt_string: The JWT token string.
        secret_or_key: The secret or public key for signature verification (optional).
        algorithms: List of allowed algorithms for verification (required if verifying).

    Returns:
        A dictionary containing:
            header: Decoded JWT header.
            payload: Decoded JWT payload (verified if possible, otherwise unverified).
            signature_verified: Boolean indicating if signature was verified (None if not attempted).
            error: Error message if parsing or verification failed.
    """
    header: dict | None = None
    unverified_payload: dict | None = None
    verified_payload: dict | None = None
    signature_verified: bool | None = None
    error: str | None = None

    try:
        # 1. Decode Header (Unverified)
        try:
            header = jwt.get_unverified_header(jwt_string)
        except Exception as e:
            error = f"Failed to decode header: {e}"
            logger.info(f"JWT header decode failed: {e}")
            return {"header": None, "payload": None, "signature_verified": None, "error": error}

        # 2. Decode Payload (Unverified)
        try:
            unverified_payload = jwt.get_unverified_claims(jwt_string)
        except Exception as e:
            error = f"Failed to decode payload: {e}"
            logger.info(f"JWT payload decode failed: {e}")
            # Still return header if it was decoded successfully
            return {"header": header, "payload": None, "signature_verified": None, "error": error}

        # 3. Verify Signature (Optional)
        if secret_or_key:
            try:
                # Determine required algorithms
                alg = header.get("alg")
                required_algorithms = algorithms if algorithms else ([alg] if alg else None)
                if not required_algorithms:
                    raise ValueError("Algorithm required for verification: specify via header or input.")

                verified_payload = jwt.decode(
                    jwt_string,
                    secret_or_key,
                    algorithms=required_algorithms,
                    # Add options if needed later
                )
                signature_verified = True
                error = None  # Clear any previous decoding error if verification succeeds
            except ValueError as ve:
                signature_verified = False
                error = str(ve)
                logger.info(f"JWT verification value error: {ve}")
            except Exception as e:
                signature_verified = False
                error = f"Signature verification failed: {e}"
                logger.info(f"JWT verification failed: {e}")

        # Determine final payload
        final_payload = verified_payload if signature_verified else unverified_payload

        # Construct result, cleaning None values
        result = {
            "header": header,
            "payload": final_payload,
            "signature_verified": signature_verified,
            "error": error,
        }
        return {k: v for k, v in result.items() if v is not None}

    except Exception as e:
        # Catch-all for unexpected errors during the process
        logger.error(f"Unexpected error parsing JWT: {e}", exc_info=True)
        return {
            "header": header,
            "payload": unverified_payload,
            "signature_verified": signature_verified,
            "error": f"An unexpected internal error occurred: {e}",
        }
