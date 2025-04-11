import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

# from models.string_obfuscator_models import ObfuscatorInput, ObfuscatorOutput # Incorrect import
# Import the actual functions and models directly from the router file
from routers.string_obfuscator_router import ObfuscatorInput  # Import model from router
from routers.string_obfuscator_router import ObfuscatorOutput  # Import model from router
from routers.string_obfuscator_router import deobfuscate_from_full_width, obfuscate_to_full_width
from routers.string_obfuscator_router import router as string_obfuscator_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(string_obfuscator_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Full-Width Obfuscation ---

# Sample strings
ASCII_STRING = "Hello World! 123 ABC abc ~?"
FULL_WIDTH_EXPECTED = "Ｈｅｌｌｏ　Ｗｏｒｌｄ！　１２３　ＡＢＣ　ａｂｃ　～？"
MIXED_STRING = "Keep this: Hello World! 123 ABC abc ~? and this too."
MIXED_FULL_WIDTH_EXPECTED = "Ｋｅｅｐ　ｔｈｉｓ：　Ｈｅｌｌｏ　Ｗｏｒｌｄ！　１２３　ＡＢＣ　ａｂｃ　～？　ａｎｄ　ｔｈｉｓ　ｔｏｏ．"  # Colon, period ARE converted
NON_ASCII_STRING = "你好世界 Español Français"
NON_ASCII_FULL_WIDTH_EXPECTED = (
    "你好世界　Ｅｓｐａñｏｌ　Ｆｒａｎçａｉｓ"  # Expect non-ASCII chars unchanged, but space converted
)


@pytest.mark.parametrize(
    "input_text, expected_obfuscated",
    [
        (ASCII_STRING, FULL_WIDTH_EXPECTED),
        (MIXED_STRING, MIXED_FULL_WIDTH_EXPECTED),
        (NON_ASCII_STRING, NON_ASCII_FULL_WIDTH_EXPECTED),  # Expect space conversion
        ("", ""),  # Empty string
        (" ", "\u3000"),  # Space to ideographic space
        ("!~", "！～"),  # Edge ASCII chars
    ],
)
@pytest.mark.asyncio
async def test_obfuscate_to_full_width_api(client: TestClient, input_text: str, expected_obfuscated: str):
    """Test the /obfuscate/full-width API endpoint."""
    payload = ObfuscatorInput(text=input_text)
    response = client.post("/api/string-obfuscator/obfuscate/full-width", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = ObfuscatorOutput(**response.json())
    assert output.result == expected_obfuscated
    # Optional: Double-check against the direct function call
    assert obfuscate_to_full_width(input_text) == expected_obfuscated


# --- Test Full-Width Deobfuscation ---


@pytest.mark.parametrize(
    "input_obfuscated, expected_deobfuscated",
    [
        (FULL_WIDTH_EXPECTED, ASCII_STRING),
        (MIXED_FULL_WIDTH_EXPECTED, MIXED_STRING),
        (NON_ASCII_STRING, NON_ASCII_STRING),  # Non-full-width chars remain unchanged
        ("", ""),  # Empty string
        ("\u3000", " "),  # Ideographic space to space
        ("！～", "!~"),  # Edge full-width chars
        # Mix of full-width and standard ASCII - should deobfuscate correctly
        (
            "Ｋｅｅｐ　ｔｈｉｓ:　Ｈｅｌｌｏ　Ｗｏｒｌｄ！　１２３　ＡＢＣ　ａｂｃ　～？　ａｎｄ　ｔｈｉｓ　ｔｏｏ.",
            MIXED_STRING,
        ),
    ],
)
@pytest.mark.asyncio
async def test_deobfuscate_from_full_width_api(client: TestClient, input_obfuscated: str, expected_deobfuscated: str):
    """Test the /deobfuscate/full-width API endpoint."""
    payload = ObfuscatorInput(text=input_obfuscated)
    response = client.post("/api/string-obfuscator/deobfuscate/full-width", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = ObfuscatorOutput(**response.json())
    assert output.result == expected_deobfuscated
    # Optional: Double-check against the direct function call
    assert deobfuscate_from_full_width(input_obfuscated) == expected_deobfuscated


# Test invalid input types (Pydantic validation)
@pytest.mark.asyncio
async def test_obfuscator_invalid_type(client: TestClient):
    """Test endpoints with invalid input type for text."""
    # Test obfuscate endpoint
    response_obf = client.post("/api/string-obfuscator/obfuscate/full-width", json={"text": 123})
    assert response_obf.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test deobfuscate endpoint
    response_deobf = client.post("/api/string-obfuscator/deobfuscate/full-width", json={"text": None})
    assert response_deobf.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
