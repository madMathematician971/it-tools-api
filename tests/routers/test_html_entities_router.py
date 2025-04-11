import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.html_entities_models import HtmlEntitiesInput, HtmlEntitiesOutput
from routers.html_entities_router import router as html_entities_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(html_entities_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test HTML Entity Encoding ---


@pytest.mark.parametrize(
    "input_text, expected_encoded",
    [
        ("<script>alert('XSS');</script>", "&lt;script&gt;alert(&#x27;XSS&#x27;);&lt;/script&gt;"),
        ("Hello & Welcome!", "Hello &amp; Welcome!"),
        ("Use \"double\" and 'single' quotes.", "Use &quot;double&quot; and &#x27;single&#x27; quotes."),
        ("No special chars here.", "No special chars here."),
        ("", ""),  # Empty string
        ("\">'<", "&quot;&gt;&#x27;&lt;"),  # Just special chars
        ("© ® ™", "© ® ™"),  # Non-ASCII chars that are not typically escaped by html.escape
    ],
)
@pytest.mark.asyncio
async def test_html_entities_encode_success(client: TestClient, input_text: str, expected_encoded: str):
    """Test successful encoding of HTML special characters."""
    payload = HtmlEntitiesInput(text=input_text)
    response = client.post("/api/html-entities/encode", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = HtmlEntitiesOutput(**response.json())
    assert output.result == expected_encoded


# --- Test HTML Entity Decoding ---


@pytest.mark.parametrize(
    "input_encoded, expected_decoded",
    [
        ("&lt;script&gt;alert(&#x27;XSS&#x27;);&lt;/script&gt;", "<script>alert('XSS');</script>"),
        ("Hello &amp; Welcome!", "Hello & Welcome!"),
        ("Use &quot;double&quot; and &#x27;single&#x27; quotes.", "Use \"double\" and 'single' quotes."),
        ("No special chars here.", "No special chars here."),
        ("", ""),  # Empty string
        ("&quot;&gt;&#x27;&lt;", "\">'<"),  # Just entities
        ("&copy; &reg; &trade;", "© ® ™"),  # Named entities
        ("&#169; &#174; &#8482;", "© ® ™"),  # Numeric entities
        ("Partially &amp; encoded & text", "Partially & encoded & text"),
        ("Invalid &entity; here", "Invalid &entity; here"),  # Invalid entities are usually passed through
    ],
)
@pytest.mark.asyncio
async def test_html_entities_decode_success(client: TestClient, input_encoded: str, expected_decoded: str):
    """Test successful decoding of HTML entities."""
    payload = HtmlEntitiesInput(text=input_encoded)
    response = client.post("/api/html-entities/decode", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = HtmlEntitiesOutput(**response.json())
    assert output.result == expected_decoded
