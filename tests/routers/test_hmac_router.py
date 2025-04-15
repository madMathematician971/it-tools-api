import hmac

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.hmac_models import HmacInput, HmacOutput
from mcp_server.tools.hmac_calculator import HASH_ALGOS
from routers.hmac_router import router as hmac_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(hmac_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test HMAC Calculation ---


@pytest.mark.parametrize(
    "text, key, algorithm",
    [
        ("message", "secretkey", "sha256"),
        ("another message", "different_key", "sha1"),
        ("hello world", "key123", "md5"),
        ("test data", "supersecret", "sha512"),
        ("", "key", "sha256"),  # Empty text
        ("message", "", "sha256"),  # Empty key
        ("", "", "sha1"),  # Empty text and key
        ("你好世界", "密码", "sha256"),  # Unicode text and key
    ],
)
@pytest.mark.asyncio
async def test_calculate_hmac_success(client: TestClient, text: str, key: str, algorithm: str):
    """Test successful HMAC calculation for various algorithms and inputs."""
    payload = HmacInput(text=text, key=key, algorithm=algorithm)
    response = client.post("/api/hmac/calculate", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = HmacOutput(**response.json())

    # Verify the HMAC against direct calculation
    text_bytes = text.encode("utf-8")
    key_bytes = key.encode("utf-8")
    hash_func = HASH_ALGOS.get(algorithm.lower())  # Use the map from the router
    assert hash_func is not None, f"Test setup error: Algorithm {algorithm} not found in HASH_ALGOS"

    expected_hmac = hmac.new(key_bytes, text_bytes, hash_func).hexdigest()
    assert output.hmac_hex == expected_hmac


@pytest.mark.asyncio
async def test_calculate_hmac_invalid_algorithm(client: TestClient):
    """Test HMAC calculation with an unsupported algorithm."""
    payload = HmacInput(text="test", key="secret", algorithm="invalid-algo")
    response = client.post("/api/hmac/calculate", json=payload.model_dump())

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported algorithm" in response.json()["detail"]
