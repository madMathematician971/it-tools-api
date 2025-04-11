import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.bip39_models import Bip39Input, Bip39Output
from routers.bip39_router import router as bip39_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(bip39_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test BIP39 Generation ---


@pytest.mark.parametrize(
    "word_count, language, expected_language_output",
    [
        (12, "en", "english"),
        (15, "en", "english"),
        (18, "en", "english"),
        (21, "en", "english"),
        (24, "en", "english"),
        # Added valid language cases previously in invalid test
        (12, "es", "spanish"),
        (12, "jp", "japanese"),
        # Note: The underlying library used might only support English ('en').
        # Add tests for other languages if the implementation supports them.
    ],
)
@pytest.mark.asyncio
async def test_bip39_generate_success(
    client: TestClient, word_count: int, language: str, expected_language_output: str
):
    """Test successful BIP39 mnemonic generation for valid word counts."""
    payload = Bip39Input(word_count=word_count, language=language)
    response = client.post("/api/bip39/generate", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = Bip39Output(**response.json())

    assert output.language == expected_language_output  # Check against expected output language
    assert output.word_count == word_count
    assert isinstance(output.mnemonic, str)

    # Check if the mnemonic has the correct number of words
    words = output.mnemonic.split()
    assert len(words) == word_count

    # Basic validation - check if all words are lowercase (standard for BIP39 English)
    if language == "en":
        assert all(word.islower() for word in words)


@pytest.mark.parametrize(
    "invalid_word_count",
    [11, 13, 16, 20, 25, 0, -12],  # Invalid word counts
)
@pytest.mark.asyncio
async def test_bip39_generate_invalid_word_count(client: TestClient, invalid_word_count: int):
    """Test BIP39 generation with invalid word counts."""
    payload = Bip39Input(word_count=invalid_word_count, language="en")
    response = client.post("/api/bip39/generate", json=payload.model_dump())

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid word_count" in response.json()["detail"]


@pytest.mark.parametrize(
    "invalid_language, expected_fallback_language",
    [
        ("nonexistent", "english"),  # Assuming only 'en' is supported by the model/underlying library
    ],
)
@pytest.mark.asyncio
async def test_bip39_generate_invalid_language(
    client: TestClient, invalid_language: str, expected_fallback_language: str
):
    """Test BIP39 generation with potentially unsupported languages (depends on implementation)."""
    # Note: This test's behavior depends on whether the Pydantic model validates the language
    # or if the underlying bip39 library handles it. The current router code doesn't
    # seem to use the language parameter for generation with the `bip39` library.
    # If the Pydantic model allows other languages, the request might succeed but ignore the language.
    payload = Bip39Input(word_count=12, language=invalid_language)
    response = client.post("/api/bip39/generate", json=payload.model_dump())

    # Adjust the assertion based on the actual model definition.
    # Use Pydantic v2 syntax to check the type annotation
    if Bip39Input.model_fields["language"].annotation is str:
        # If language is just a string, the API likely succeeds but uses the fallback (English)
        assert response.status_code == status.HTTP_200_OK
        output = Bip39Output(**response.json())
        assert output.language == expected_fallback_language  # Check for fallback language
        assert output.word_count == 12
        assert len(output.mnemonic.split()) == 12
