import bcrypt
import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.bcrypt_models import BcryptHashInput, BcryptHashOutput, BcryptVerifyInput, BcryptVerifyOutput
from routers.bcrypt_router import router as bcrypt_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(bcrypt_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Bcrypt Hashing ---


@pytest.mark.parametrize(
    "password, salt_rounds",
    [
        ("mypassword", 12),
        ("complexP@$$w0rd", 10),
        ("!@#$%^&*()_+", 14),
        ("", 4),  # Test minimum salt rounds and empty password
    ],
)
@pytest.mark.asyncio
async def test_bcrypt_hash_success(client: TestClient, password: str, salt_rounds: int):
    """Test successful password hashing with various salt rounds."""
    payload = BcryptHashInput(password=password, salt_rounds=salt_rounds)
    response = client.post("/api/bcrypt/hash", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = BcryptHashOutput(**response.json())

    # Verify the hash looks like a bcrypt hash (starts with $2b$)
    assert output.hash.startswith("$2b$")

    # Verify the hash can be verified with the original password
    assert bcrypt.checkpw(password.encode("utf-8"), output.hash.encode("utf-8"))


# Test hashing with invalid salt rounds (should be caught by Pydantic validator)
@pytest.mark.parametrize("invalid_salt_rounds", [3, 32])
@pytest.mark.asyncio
async def test_bcrypt_hash_invalid_salt_rounds(client: TestClient, invalid_salt_rounds: int):
    """Test hashing with salt rounds outside the allowed range (4-31)."""
    payload = {"password": "test", "salt_rounds": invalid_salt_rounds}
    response = client.post("/api/bcrypt/hash", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# --- Test Bcrypt Verification ---


@pytest.mark.asyncio
async def test_bcrypt_verify_success(client: TestClient):
    """Test successful password verification."""
    password = "verifythispassword"
    # Manually hash for comparison
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    payload = BcryptVerifyInput(password=password, hash=hashed_pw.decode("utf-8"))
    response = client.post("/api/bcrypt/verify", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = BcryptVerifyOutput(**response.json())
    assert output.match is True


@pytest.mark.asyncio
async def test_bcrypt_verify_failure(client: TestClient):
    """Test verification failure with incorrect password."""
    password = "correctpassword"
    incorrect_password = "wrongpassword"
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    payload = BcryptVerifyInput(password=incorrect_password, hash=hashed_pw.decode("utf-8"))
    response = client.post("/api/bcrypt/verify", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = BcryptVerifyOutput(**response.json())
    assert output.match is False


@pytest.mark.asyncio
async def test_bcrypt_verify_invalid_hash(client: TestClient):
    """Test verification with an invalid hash format."""
    payload = BcryptVerifyInput(password="test", hash="invalid-hash-format")
    response = client.post("/api/bcrypt/verify", json=payload.model_dump())

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid hash format provided."
