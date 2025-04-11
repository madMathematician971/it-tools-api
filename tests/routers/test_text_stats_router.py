import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.text_stats_models import TextStatsInput, TextStatsOutput
from routers.text_stats_router import router as text_stats_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(text_stats_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Text Statistics Calculation ---


@pytest.mark.parametrize(
    "input_text, expected_stats",
    [
        # Basic case
        (
            "Hello world! This is a test. One more sentence.",
            {
                "char_count": 47,
                "char_count_no_spaces": 39,
                "word_count": 9,
                "line_count": 1,
                "sentence_count": 3,
                "paragraph_count": 1,
            },
        ),
        # Multiple lines and paragraphs
        (
            "Paragraph 1, line 1.\nParagraph 1, line 2.\n\nParagraph 2.\nSentence 2.1? Sentence 2.2!",
            {
                "char_count": 83,
                "char_count_no_spaces": 69,
                "word_count": 14,
                "line_count": 5,
                "sentence_count": 4,
                "paragraph_count": 2,
            },
        ),
        # Empty string
        (
            "",
            {
                "char_count": 0,
                "char_count_no_spaces": 0,
                "word_count": 0,
                "line_count": 0,
                "sentence_count": 0,
                "paragraph_count": 0,
            },
        ),
        # String with only spaces/newlines
        (
            "   \n \n  ",
            {
                "char_count": 8,
                "char_count_no_spaces": 0,
                "word_count": 0,
                "line_count": 3,
                "sentence_count": 0,
                "paragraph_count": 0,
            },
        ),
        # Single word
        (
            "Word",
            {
                "char_count": 4,
                "char_count_no_spaces": 4,
                "word_count": 1,
                "line_count": 1,
                "sentence_count": 1,  # Counts as 1 sentence
                "paragraph_count": 1,  # Counts as 1 paragraph
            },
        ),
        # Text ending without punctuation (counts as one sentence)
        (
            "This ends abruptly",
            {
                "char_count": 18,
                "char_count_no_spaces": 16,
                "word_count": 3,
                "line_count": 1,
                "sentence_count": 1,
                "paragraph_count": 1,
            },
        ),
        # Edge cases for sentence splitting (e.g., Mr. Smith)
        (
            "Mr. Smith went to Washington. It was nice.",
            {
                "char_count": 42,
                "char_count_no_spaces": 35,
                "word_count": 8,
                "line_count": 1,
                "sentence_count": 2,  # Regex should handle Mr. correctly
                "paragraph_count": 1,
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_calculate_text_stats_success(client: TestClient, input_text: str, expected_stats: dict):
    """Test successful calculation of text statistics for various inputs."""
    payload = TextStatsInput(text=input_text)
    response = client.post("/api/text/stats", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = TextStatsOutput(**response.json())

    assert output.stats == expected_stats


# Test invalid input types (Pydantic validation)
@pytest.mark.asyncio
async def test_calculate_text_stats_invalid_type(client: TestClient):
    """Test providing invalid type for text input."""
    response = client.post("/api/text/stats", json={"text": 1234})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Update expected substring based on Pydantic error
    expected_error_substring = "input should be a valid string"
    assert expected_error_substring.lower() in str(response.json()).lower()
