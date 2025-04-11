import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.numeronym_models import NumeronymInput, NumeronymOutput
from routers.numeronym_router import router as numeronym_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(numeronym_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Numeronym Conversion ---


@pytest.mark.parametrize(
    "text, mode, expected_result",
    [
        # Convert mode
        ("internationalization", "convert", "i18n"),
        ("localization", "convert", "l10n"),
        ("accessibility", "convert", "a11y"),
        ("kubernetes", "convert", "k8s"),
        ("A long word sentence here", "convert", "A l2g w2d s6e h2e"),
        ("Short words are ok", "convert", "S3t w3s are ok"),  # words < 4 chars kept
        ("Keep123Numbers", "convert", "K12s"),  # Handles numbers within word
        ("Word. With Punctuation!", "convert", "W2d. W2h P9n!"),  # Updated P8n -> P9n
        # Decode mode (approximate)
        ("i18n", "decode", "i__________________n"),
        ("l10n", "decode", "l__________n"),
        ("a11y", "decode", "a___________y"),
        ("k8s", "decode", "k________s"),
        ("A l2g w2d s6e h2e", "decode", "A l__g w__d s______e h__e"),
        ("S3t w3s are ok", "decode", "S___t w___s are ok"),  # Words not matching format are kept
        ("notanumeronym", "decode", "notanumeronym"),  # No change if not numeronym format
    ],
)
@pytest.mark.asyncio
async def test_numeronym_convert_decode(client: TestClient, text: str, mode: str, expected_result: str):
    """Test both converting to numeronyms and decoding them."""
    payload = NumeronymInput(text=text, mode=mode)
    response = client.post("/api/numeronym/", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = NumeronymOutput(**response.json())

    assert output.original == text
    assert output.result == expected_result
    assert output.mode == mode


@pytest.mark.parametrize(
    "text, mode, error_substring",
    [
        ("Some text", "invalid_mode", "Invalid mode"),
        ("", "convert", "Input text cannot be empty"),
        ("", "decode", "Input text cannot be empty"),
    ],
)
@pytest.mark.asyncio
async def test_numeronym_invalid_input(client: TestClient, text: str, mode: str, error_substring: str):
    """Test invalid inputs like bad mode or empty text."""
    payload = NumeronymInput(text=text, mode=mode)
    response = client.post("/api/numeronym/", json=payload.model_dump())

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_detail = response.json().get("detail", "")
    if isinstance(response_detail, list):
        assert any(
            error_substring in err.get("msg", "") for err in response_detail
        ), f"Expected '{error_substring}' not found in {response_detail}"
    else:
        assert error_substring in response_detail, f"Expected '{error_substring}' not found in {response_detail}"
