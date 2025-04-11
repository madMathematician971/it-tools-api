import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.token_models import CharSetType, TokenInput, TokenOutput
from routers.token_router import CHARSET_MAP
from routers.token_router import router as token_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(token_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Token Generation ---


@pytest.mark.parametrize(
    "length, count, charset_type",
    [
        (16, 1, CharSetType.alphanumeric),  # Default case
        (32, 5, CharSetType.alphanumeric),
        (8, 10, CharSetType.alpha),
        (6, 2, CharSetType.numeric),
        (10, 3, CharSetType.hex_lower),
        (12, 1, CharSetType.hex_upper),
        (1, 1, CharSetType.alphanumeric),  # Minimum length
        (100, 1, CharSetType.alphanumeric),  # Reasonable max length
        (16, 1, CharSetType.alphanumeric),  # Minimum count
        (10, 10, CharSetType.alphanumeric),  # Max count (adjust if model changes)
    ],
)
@pytest.mark.asyncio
async def test_generate_tokens_success(client: TestClient, length: int, count: int, charset_type: CharSetType):
    """Test successful token generation with various options."""
    payload = TokenInput(length=length, count=count, charset_type=charset_type)
    response = client.post("/api/token/generate", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = TokenOutput(**response.json())

    assert isinstance(output.tokens, list)
    assert len(output.tokens) == count

    expected_charset = CHARSET_MAP[charset_type]
    for token in output.tokens:
        assert isinstance(token, str)
        assert len(token) == length
        # Verify all characters in the token belong to the expected charset
        assert all(c in expected_charset for c in token)


@pytest.mark.parametrize(
    "payload_update, error_substring",
    [
        ({"length": 0}, "Input should be greater than 0"),
        # ({'length': 1000}, 'ensure this value is less than or equal to'), # Add if max length constraint exists
        ({"count": 0}, "Input should be greater than 0"),
        # ({'count': 101}, 'ensure this value is less than or equal to'), # Add if max count constraint exists
        ({"charset_type": "invalid"}, "Input should be 'alphanumeric', 'alpha', 'numeric', 'hex_lower' or 'hex_upper'"),
    ],
)
@pytest.mark.asyncio
async def test_generate_tokens_invalid_input(client: TestClient, payload_update: dict, error_substring: str):
    """Test token generation with invalid input values (caught by Pydantic)."""
    base_payload = {
        "length": 16,
        "count": 1,
        "charset_type": CharSetType.alphanumeric,
    }
    invalid_payload_dict = {**base_payload, **payload_update}

    response = client.post("/api/token/generate", json=invalid_payload_dict)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Use case-insensitive comparison
    assert error_substring.lower() in str(response.json()).lower()
