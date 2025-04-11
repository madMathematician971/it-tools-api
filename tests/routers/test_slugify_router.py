import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.slugify_models import SlugifyInput, SlugifyOutput
from routers.slugify_router import router as slugify_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(slugify_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Slugify Creation ---


@pytest.mark.parametrize(
    "input_text, expected_slug",
    [
        ("Hello World", "hello-world"),
        ("This is a Test String!", "this-is-a-test-string"),
        ("  Leading and Trailing Spaces  ", "leading-and-trailing-spaces"),
        ("Special Chars: !@#$%^&*()_+=", "special-chars"),  # Removes most special chars
        ("Unicode: äöüß", "unicode-aouss"),  # Basic transliteration
        ("Repeated---Hyphens", "repeated-hyphens"),  # Collapses multiple hyphens
        ("Already-slugified", "already-slugified"),  # Handles existing hyphens
        ("Numbers 123 and text", "numbers-123-and-text"),
        ("UPPERCASE TEXT", "uppercase-text"),  # Converts to lowercase
        ("", ""),  # Empty string
    ],
)
@pytest.mark.asyncio
async def test_create_slug_success(client: TestClient, input_text: str, expected_slug: str):
    """Test successful slug creation for various inputs."""
    payload = SlugifyInput(text=input_text)
    response = client.post("/api/slugify/create", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = SlugifyOutput(**response.json())
    assert output.slug == expected_slug


# Test for potentially invalid input type (should be caught by Pydantic)
@pytest.mark.asyncio
async def test_create_slug_invalid_type(client: TestClient):
    """Test providing invalid type for text input."""
    response = client.post("/api/slugify/create", json={"text": 12345})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
