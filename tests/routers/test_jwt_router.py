import time

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from jose import jwt

from models.jwt_models import JwtInput, JwtOutput
from routers.jwt_router import router as jwt_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(jwt_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test JWT Parsing ---

# Sample keys and tokens
SECRET_KEY = "your-secret-key-here"
ALGORITHM_HS256 = "HS256"
ALGORITHM_RS256 = "RS256"

# Generate RSA keys for testing RS256
private_key_pem = (
    "-----BEGIN PRIVATE KEY-----\n"  # Replace with a real test private key if needed
    "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDaG3v4wQYf\n"
    "... (rest of a dummy key) ...\n"
    "-----END PRIVATE KEY-----\n"
)
public_key_pem = (
    "-----BEGIN PUBLIC KEY-----\n"  # Replace with a real test public key if needed
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2ht7+MEGH/N13wkJ\n"
    "... (rest of a dummy key) ...\n"
    "-----END PUBLIC KEY-----\n"
)

# Use a known good library (jose) to generate test tokens
payload_data = {"user_id": 123, "username": "testuser", "exp": int(time.time()) + 3600}
payload_data_expired = {"user_id": 456, "username": "expireduser", "exp": int(time.time()) - 3600}

token_hs256 = jwt.encode(payload_data, SECRET_KEY, algorithm=ALGORITHM_HS256)
token_hs256_expired = jwt.encode(payload_data_expired, SECRET_KEY, algorithm=ALGORITHM_HS256)
# token_rs256 = jwt.encode(payload_data, private_key_pem, algorithm=ALGORITHM_RS256) # Requires real keys
# For now, use a placeholder if real keys aren't available
token_rs256_placeholder = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjMsInVzZXJuYW1lIjoidGVzdHVzZXIiLCJleHAiOjE3MDAwMDAwMDB9.SignaturePlaceholder"
token_invalid_sig = token_hs256[:-5] + "xxxxx"
token_invalid_format = "this.is.not.a.jwt"


@pytest.mark.parametrize(
    "jwt_string, secret_or_key, algorithms, expected_error, expect_verified, expected_payload",
    [
        # HS256 - Valid signature
        (token_hs256, SECRET_KEY, [ALGORITHM_HS256], None, True, payload_data),
        # HS256 - No secret provided (decode only)
        (token_hs256, None, None, None, None, payload_data),
        # HS256 - Wrong secret
        (token_hs256, "wrong-secret", [ALGORITHM_HS256], "Signature verification failed", False, payload_data),
        # HS256 - Expired signature
        (token_hs256_expired, SECRET_KEY, [ALGORITHM_HS256], "Signature has expired", False, payload_data_expired),
        # HS256 - Invalid signature
        (token_invalid_sig, SECRET_KEY, [ALGORITHM_HS256], "Signature verification failed", False, payload_data),
        # HS256 - Algorithm mismatch (header says HS256, asked to verify with RS256)
        (
            token_hs256,
            SECRET_KEY,
            [ALGORITHM_RS256],
            "Error during verification process: The specified alg value is not allowed",
            False,
            payload_data,
        ),
        # RS256 - Valid signature (using placeholder - this test will likely fail verification without real keys)
        # (token_rs256_placeholder, public_key_pem, [ALGORITHM_RS256], None, True, payload_data), # Uncomment if using real keys
        # RS256 - No key provided (decode only)
        (token_rs256_placeholder, None, None, None, None, payload_data),
        # RS256 - Wrong key (using HS key for RS token)
        (
            token_rs256_placeholder,
            SECRET_KEY,
            [ALGORITHM_RS256],
            "Error during verification process",
            False,
            payload_data,
        ),
        # Invalid JWT format
        (token_invalid_format, None, None, "Failed to decode header: Error decoding token headers", None, None),
        ("a.b", None, None, "Failed to decode header: Error decoding token headers", None, None),  # Too few parts
    ],
)
@pytest.mark.asyncio
async def test_parse_jwt(
    client: TestClient,
    jwt_string: str,
    secret_or_key: str | None,
    algorithms: list[str] | None,
    expected_error: str | None,
    expect_verified: bool | None,
    expected_payload: dict | None,
):
    """Test JWT parsing and verification with various scenarios."""
    payload = JwtInput(jwt_string=jwt_string, secret_or_key=secret_or_key, algorithms=algorithms)
    response = client.post("/api/jwt/parse", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output_dict = response.json()
    # Recreate the model to handle Optional fields correctly
    output = JwtOutput(**output_dict)

    if expected_error:
        assert output.error is not None
        assert expected_error in output.error
        # If verification failed, signature_verified should be False (unless header/payload parse failed first)
        if "Signature" in expected_error or "verification" in expected_error:
            assert output.signature_verified is False
        if "header" in expected_error:
            assert output.header is None
        if "payload" in expected_error:
            assert output.payload is None
    else:
        assert output.error is None
        assert output.header is not None
        assert output.payload is not None
        # Compare payloads (ignoring 'exp' differences if subtle due to timing)
        if expected_payload:
            # Deep comparison, maybe excluding 'exp' or using tolerance
            payload_copy = output.payload.copy()
            expected_copy = expected_payload.copy()
            payload_copy.pop("exp", None)
            expected_copy.pop("exp", None)
            assert payload_copy == expected_copy

        assert output.signature_verified == expect_verified
