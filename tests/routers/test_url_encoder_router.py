import urllib.parse

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.url_encoder_models import UrlEncoderInput, UrlEncoderOutput
from routers.url_encoder_router import router as url_encoder_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(url_encoder_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test URL Encoding/Decoding ---

# Sample data
PLAIN_TEXT = "Hello World! This has spaces & special chars?"
ENCODED_TEXT = urllib.parse.quote(PLAIN_TEXT, safe="")
PARTIALLY_ENCODED = "Hello%20World%21%20This%20has%20spaces%20%26%20special%20chars%3F"


@pytest.mark.parametrize(
    "mode, input_text, expected_result",
    [
        # Encoding
        ("encode", PLAIN_TEXT, ENCODED_TEXT),
        ("encode", "simple", "simple"),  # No special chars
        ("encode", "", None),  # Handled by error case
        ("encode", "http://example.com/?q=test value", "http%3A%2F%2Fexample.com%2F%3Fq%3Dtest%20value"),
        # Decoding
        ("decode", ENCODED_TEXT, PLAIN_TEXT),
        ("decode", PARTIALLY_ENCODED, PLAIN_TEXT),
        ("decode", "simple", "simple"),  # No encoded chars
        ("decode", "", None),  # Handled by error case
        ("decode", "http%3A%2F%2Fexample.com%2F%3Fq%3Dtest%20value", "http://example.com/?q=test value"),
        # Decoding with potentially invalid sequences (urllib handles many gracefully)
        ("decode", "%E0%A4%A", "�%A"),  # Incomplete UTF-8 sequence
        ("decode", "%ZZinvalid", "%ZZinvalid"),  # Invalid hex
    ],
)
@pytest.mark.asyncio
async def test_url_encoder_success(client: TestClient, mode: str, input_text: str, expected_result: str | None):
    """Test successful URL encoding and decoding."""
    if expected_result is None:  # Skip cases handled by error tests
        return

    payload = UrlEncoderInput(text=input_text, mode=mode)
    response = client.post("/api/url-encoder/", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = UrlEncoderOutput(**response.json())

    assert output.original == input_text
    assert output.result == expected_result
    assert output.mode == mode
    assert output.error is None


@pytest.mark.parametrize(
    "mode, input_text, expected_status, error_substring",
    [
        ("encode", "", status.HTTP_400_BAD_REQUEST, "Input text cannot be empty"),
        ("decode", "   ", status.HTTP_400_BAD_REQUEST, "Input text cannot be empty"),  # Trimmed is empty
        ("invalid_mode", "test", status.HTTP_400_BAD_REQUEST, "Invalid mode"),
        # Pydantic validation
        (None, "test", status.HTTP_422_UNPROCESSABLE_ENTITY, "field required"),
    ],
)
@pytest.mark.asyncio
async def test_url_encoder_errors(
    client: TestClient, mode: str | None, input_text: str, expected_status: int, error_substring: str
):
    """Test error handling for invalid mode, empty input, or Pydantic validation."""
    payload_dict = {"text": input_text, "mode": mode}
    if mode is None:
        payload_dict.pop("mode")

    response = client.post("/api/url-encoder/", json=payload_dict)

    assert response.status_code == expected_status
    if expected_status == status.HTTP_422_UNPROCESSABLE_ENTITY:
        assert error_substring in str(response.json()).lower()
    else:
        assert error_substring in response.json()["detail"]
