import re

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.lorem_models import LoremInput, LoremOutput, LoremType
from routers.lorem_router import router as lorem_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(lorem_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Lorem Ipsum Generation ---


@pytest.mark.parametrize(
    "lorem_type, count",
    [
        (LoremType.words, 10),
        (LoremType.words, 1),
        (LoremType.words, 100),
        (LoremType.sentences, 3),
        (LoremType.sentences, 1),
        (LoremType.paragraphs, 2),
        (LoremType.paragraphs, 1),
    ],
)
@pytest.mark.asyncio
async def test_generate_lorem_success(client: TestClient, lorem_type: LoremType, count: int):
    """Test successful generation of words, sentences, and paragraphs."""
    payload = LoremInput(lorem_type=lorem_type, count=count)
    response = client.post("/api/lorem/generate", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = LoremOutput(**response.json())

    assert isinstance(output.text, str)
    assert len(output.text) > 0  # Should generate something

    # Basic structural checks based on type
    if lorem_type == LoremType.words:
        # Check number of words (approximate, might vary slightly)
        words = output.text.split()
        assert len(words) >= count - 1 and len(words) <= count + 1  # Allow slight variation
        assert "." not in output.text  # Should generally not contain sentence endings
    elif lorem_type == LoremType.sentences:
        # Check for sentence endings (e.g., '.')
        # Count sentences roughly by counting periods.
        # This is approximate as the library might use other punctuation.
        sentence_endings = len(re.findall(r"[.!?]", output.text))
        assert sentence_endings >= count
    elif lorem_type == LoremType.paragraphs:
        # Check for paragraph breaks (double newline)
        paragraphs = output.text.split("\n\n")
        assert len(paragraphs) == count


@pytest.mark.parametrize(
    "lorem_type, count, error_substring",
    [
        (LoremType.words, 0, "Input should be greater than 0"),  # Pydantic v2 error message
        (LoremType.sentences, -1, "Input should be greater than 0"),  # Pydantic v2 error message
        ("invalid_type", 5, "Input should be 'words', 'sentences' or 'paragraphs'"),  # Pydantic v2 enum error
    ],
)
@pytest.mark.asyncio
async def test_generate_lorem_invalid_input(
    client: TestClient, lorem_type: str | LoremType, count: int, error_substring: str
):
    """Test lorem generation with invalid input (caught by Pydantic)."""
    # Use dict directly to allow invalid enum value for testing
    payload_dict = {"lorem_type": lorem_type, "count": count}
    response = client.post("/api/lorem/generate", json=payload_dict)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Check if the specific error message substring is present in the response detail
    response_detail = str(response.json().get("detail", ""))
    assert (
        error_substring.lower() in response_detail.lower()
    ), f"Expected '{error_substring}' in validation error, but got: {response_detail}"
