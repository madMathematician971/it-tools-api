import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.nato_alphabet_models import NatoInput, NatoOutput
from routers.nato_alphabet_router import NATO_ALPHABET
from routers.nato_alphabet_router import router as nato_alphabet_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(nato_alphabet_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test NATO Conversion (Text to NATO) ---


@pytest.mark.parametrize(
    "text, fmt, separator, include_original, lowercase, expected_output_substrings",
    [
        # Basic text format
        ("ABC", "text", " ", False, False, ["Alpha Bravo Charlie"]),
        ("Hi!", "text", "-", False, False, ["Hotel-India-Exclamation Mark"]),
        ("Test 123", "text", " ", False, False, ["Tango Echo Sierra Tango Space One Two Three"]),
        # Text format with lowercase
        ("abc", "text", " ", False, True, ["alpha bravo charlie"]),
        # Text format with original char included
        ("A B", "text", " ", True, False, ["A - Alpha   - Space B - Bravo"]),
        ("Z", "text", " ", True, True, ["Z - zulu"]),
        # List format
        ("Go", "list", " ", False, False, ["• Golf", "• Oscar"]),
        ("X-Y", "list", " ", True, False, ["• X - X-ray", "• - - Dash", "• Y - Yankee"]),
        # Table format
        ("12", "table", " ", False, False, ["One", "Two"]),
        ("OK?", "table", " ", True, False, ["O - Oscar", "K - Kilo", "? - Question Mark"]),
        # Special characters
        (".@", "text", " ", False, False, ["Period At Sign"]),
        # Unknown character
        ("A£B", "text", " ", False, False, ["Alpha Unknown (£) Bravo"]),
    ],
)
@pytest.mark.asyncio
async def test_convert_to_nato_success(
    client: TestClient,
    text: str,
    fmt: str,
    separator: str,
    include_original: bool,
    lowercase: bool,
    expected_output_substrings: list[str],
):
    """Test successful conversion from text to NATO phonetic alphabet."""
    payload = NatoInput(
        text=text, format=fmt, separator=separator, include_original=include_original, lowercase=lowercase
    )
    response = client.post("/api/nato-alphabet/", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = NatoOutput(**response.json())

    assert output.input == text
    assert output.format == fmt
    assert isinstance(output.character_map, dict)

    # Check output contains expected parts
    for substring in expected_output_substrings:
        assert substring in output.output

    # Check character map
    for char in text:
        assert char in output.character_map
        expected_nato = NATO_ALPHABET.get(char.upper(), f"Unknown ({char})")
        assert output.character_map[char] == expected_nato


@pytest.mark.asyncio
async def test_convert_to_nato_empty_input(client: TestClient):
    """Test error handling for empty input text."""
    payload = NatoInput(text="", format="text", separator=" ", include_original=False, lowercase=False)
    response = client.post("/api/nato-alphabet/", json=payload.model_dump())
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Input text cannot be empty" in response.json()["detail"]


# --- Test NATO Decoding (NATO to Text) ---
# Note: The decoding endpoint is currently commented out in the router.
#       If uncommented, these tests would apply.

# @pytest.mark.parametrize(
#     "nato_text, separator, expected_result",
#     [
#         ("Alpha Bravo Charlie", " ", "ABC"),
#         ("Hotel-India-Exclamation Mark", "-", "Hi!"),
#         ("Tango Echo Sierra Tango Space One Two Three", " ", "TEST 123"),
#         ("alpha bravo charlie", " ", "abc"), # Lowercase input
#         ("Period At Sign", " ", ".@"),
#         ("Xray Yankee Zulu", " ", "XYZ"), # Using Xray variation
#         ("Unknown Alpha Unknown", " ", "?A?"), # Unknown words
#         ("AlphaBravoCharlie", "", "ABC"), # No separator
#         ("Alpha  Bravo   Charlie", " ", "ABC"), # Multiple spaces as separator
#     ]
# )
# @pytest.mark.asyncio
# async def test_nato_to_text_success(client: TestClient, nato_text: str, separator: str, expected_result: str):
#     """Test successful decoding from NATO words back to text."""
#     # The payload model might need adjustment if decode uses a different one
#     payload = NatoInput(text=nato_text, separator=separator, format='text', include_original=False, lowercase=False)
#     response = client.post("/api/nato-alphabet/decode", json=payload.model_dump())
#
#     assert response.status_code == status.HTTP_200_OK
#     # Assuming decode also returns NatoOutput, but maybe just the result?
#     # Adjust based on actual implementation
#     output = NatoOutput(**response.json())
#     assert output.result == expected_result # Or output.output, depending on model
#
# @pytest.mark.asyncio
# async def test_nato_to_text_empty_input(client: TestClient):
#     """Test NATO decoding with empty input."""
#     payload = NatoInput(text="", separator=" ", format='text', include_original=False, lowercase=False)
#     response = client.post("/api/nato-alphabet/decode", json=payload.model_dump())
#     assert response.status_code == status.HTTP_200_OK
#     output = NatoOutput(**response.json())
#     assert output.result == "" # Expect empty string for empty input
