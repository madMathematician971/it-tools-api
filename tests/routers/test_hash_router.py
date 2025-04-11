import hashlib

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.hash_models import HashInput, HashOutput
from routers.hash_router import router as hash_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(hash_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Hash Calculation ---


@pytest.mark.parametrize(
    "input_text",
    [
        "hello world",
        "This is a test string.",
        "",  # Empty string
        "1234567890",
        "~!@#$%^&*()_+`-={}|[]\\:\"'<>?,./",  # String with many special chars
        "你好世界",  # Unicode string
    ],
)
@pytest.mark.asyncio
async def test_calculate_hashes_success(client: TestClient, input_text: str):
    """Test successful calculation of all hash types."""
    payload = HashInput(text=input_text)
    response = client.post("/api/hash/calculate", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = HashOutput(**response.json())

    # Verify each hash against direct calculation using hashlib
    text_bytes = input_text.encode("utf-8")
    expected_md5 = hashlib.md5(text_bytes).hexdigest()
    expected_sha1 = hashlib.sha1(text_bytes).hexdigest()
    expected_sha256 = hashlib.sha256(text_bytes).hexdigest()
    expected_sha512 = hashlib.sha512(text_bytes).hexdigest()

    assert output.md5 == expected_md5
    assert output.sha1 == expected_sha1
    assert output.sha256 == expected_sha256
    assert output.sha512 == expected_sha512


# Test with non-string input (should be caught by Pydantic)
@pytest.mark.asyncio
async def test_calculate_hashes_invalid_input_type(client: TestClient):
    """Test providing invalid type for the input text."""
    response = client.post("/api/hash/calculate", json={"text": 12345})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
