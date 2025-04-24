import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from mcp_server.tools.nato_converter import NATO_ALPHABET
from models.nato_alphabet_models import NatoInput, NatoOutput
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
        ("Test 123", "text", " ", False, False, ["Tango Echo Sierra Tango Space 1 2 3"]),
        # Text format with lowercase
        ("abc", "text", " ", False, True, ["alpha bravo charlie"]),
        # Text format with original char included
        ("A B", "text", " ", True, False, ["Alpha Space Bravo"]),
        ("Z", "text", " ", True, True, ["zulu"]),
        # List format
        ("Go", "list", " ", False, False, ["Golf", "Oscar"]),
        ("X-Y", "list", " ", True, False, ["X-ray", "Dash", "Yankee"]),
        ("12", "list", " ", False, False, ["1", "2"]),
        ("OK?", "list", " ", True, False, ["Oscar", "Kilo", "Question Mark"]),
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
        text=text, output_format=fmt, separator=separator, include_original=include_original, lowercase=lowercase
    )
    response = client.post("/api/nato-alphabet/to-nato", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = NatoOutput(**response.json())

    assert output.input == text
    assert output.output_format == fmt
    assert isinstance(output.character_map, dict)

    # Check output content based on format
    if fmt == "list":
        assert isinstance(output.output, list)
        assert output.output == expected_output_substrings  # Direct list comparison
    else:  # text format
        assert isinstance(output.output, str)
        # Check output contains expected parts for text format
        content_for_check = output.output
        for substring in expected_output_substrings:
            assert substring in content_for_check

    # Check character map
    for char in text:
        assert char in output.character_map
        expected_nato = NATO_ALPHABET.get(char.upper(), f"Unknown ({char})") if not char.isdigit() else char
        assert output.character_map[char] == expected_nato


@pytest.mark.asyncio
async def test_convert_to_nato_empty_input(client: TestClient):
    """Test error handling for empty input text."""
    payload = NatoInput(text="", output_format="text", separator=" ", include_original=False, lowercase=False)
    response = client.post("/api/nato-alphabet/to-nato", json=payload.model_dump())
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Input text cannot be empty" in response.json()["detail"]


# --- Test NATO Decoding (NATO to Text) ---


@pytest.mark.parametrize(
    "nato_text, separator, expected_result",
    [
        ("Alpha Bravo Charlie", " ", "ABC"),
        ("Hotel-India-Exclamation Mark", "-", "HI!"),
        ("Tango Echo Sierra Tango Space 1 2 3", " ", "TEST 123"),
        ("alpha bravo charlie", " ", "ABC"),
        ("Period At Sign", " ", ".@"),
        ("Xray Yankee Zulu", " ", "XYZ"),  # Using Xray variation
        ("Unknown Alpha Unknown", " ", "?A?"),  # Unknown words
        ("AlphaBravoCharlie", "", None),  # Expect error/None for empty separator
        ("Alpha  Bravo   Charlie", " ", "ABC"),  # Multiple spaces as separator
    ],
)
@pytest.mark.asyncio
async def test_nato_to_text_success(client: TestClient, nato_text: str, separator: str, expected_result: str | None):
    """Test successful decoding from NATO words back to text."""
    # The payload model might need adjustment if decode uses a different one
    payload = NatoInput(
        text=nato_text, separator=separator, output_format="text", include_original=False, lowercase=False
    )
    response = client.post("/api/nato-alphabet/from-nato", json=payload.model_dump())

    # Check for expected error with empty separator
    if separator == "":
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Empty separator is not allowed" in response.json()["detail"]
    else:
        assert response.status_code == status.HTTP_200_OK
        output = NatoOutput(**response.json())
        assert output.output == expected_result  # Check the 'output' field


@pytest.mark.asyncio
async def test_nato_to_text_empty_input(client: TestClient):
    """Test NATO decoding with empty input."""
    payload = NatoInput(text="", separator=" ", output_format="text", include_original=False, lowercase=False)
    response = client.post("/api/nato-alphabet/from-nato", json=payload.model_dump())
    assert response.status_code == status.HTTP_200_OK
    output = NatoOutput(**response.json())
    assert output.output == ""  # Expect empty string for empty input
