import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.rsa_models import RsaKeygenOutput
from routers.rsa_router import router as rsa_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(rsa_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test RSA Key Generation ---


@pytest.mark.parametrize("key_size", [1024, 2048, 4096])  # Test common key sizes
@pytest.mark.asyncio
async def test_generate_rsa_keys_success(client: TestClient, key_size: int):
    """Test successful generation of RSA key pairs for different sizes."""
    response = client.post("/api/rsa/generate-keys", json={"key_size": key_size})

    assert response.status_code == status.HTTP_200_OK
    output = RsaKeygenOutput(**response.json())

    assert output.key_size == key_size
    assert isinstance(output.private_key_pem, str)
    assert isinstance(output.public_key_pem, str)

    # Basic PEM format checks
    assert output.private_key_pem.startswith("-----BEGIN PRIVATE KEY-----")
    assert output.private_key_pem.strip().endswith("-----END PRIVATE KEY-----")
    assert output.public_key_pem.startswith("-----BEGIN PUBLIC KEY-----")
    assert output.public_key_pem.strip().endswith("-----END PUBLIC KEY-----")

    # Try loading the keys to verify format correctness
    try:
        private_key = serialization.load_pem_private_key(
            output.private_key_pem.encode("utf-8"), password=None  # Assuming no encryption
        )
        assert isinstance(private_key, rsa.RSAPrivateKey)
        assert private_key.key_size == key_size

        public_key = serialization.load_pem_public_key(
            output.public_key_pem.encode("utf-8"),
        )
        assert isinstance(public_key, rsa.RSAPublicKey)
        assert public_key.key_size == key_size

    except Exception as e:
        pytest.fail(f"Failed to load generated PEM keys (size {key_size}): {e}")


@pytest.mark.parametrize(
    "invalid_key_size, error_substring",
    [
        # All invalid sizes should trigger the same Literal error
        (512, "Input should be 1024, 2048 or 4096"),
        (1025, "Input should be 1024, 2048 or 4096"),
        (2047, "Input should be 1024, 2048 or 4096"),
    ],
)
@pytest.mark.asyncio
async def test_generate_rsa_keys_invalid_size(client: TestClient, invalid_key_size: int, error_substring: str):
    """Test key generation with invalid key sizes."""
    payload = {"key_size": invalid_key_size}  # Use dict for Pydantic validation
    response = client.post("/api/rsa/generate-keys", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Use case-insensitive comparison
    assert error_substring.lower() in str(response.json()).lower()
