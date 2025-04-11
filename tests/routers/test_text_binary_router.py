import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.text_binary_models import TextBinaryInput, TextBinaryOutput

# Import helper functions for validation/comparison
from routers.text_binary_router import router as text_binary_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(text_binary_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Text to Binary Conversion ---

# Sample data
TEXT_INPUT = "Hi!"
BINARY_EXPECTED_SPACES = "01001000 01101001 00100001"
BINARY_EXPECTED_NOSPACES = "010010000110100100100001"


@pytest.mark.parametrize(
    "input_text, include_spaces, expected_binary",
    [
        (TEXT_INPUT, True, BINARY_EXPECTED_SPACES),
        (TEXT_INPUT, False, BINARY_EXPECTED_NOSPACES),
        ("A", True, "01000001"),
        ("A", False, "01000001"),
        (" spaces ", True, "00100000 01110011 01110000 01100001 01100011 01100101 01110011 00100000"),
        (" spaces ", False, "0010000001110011011100000110000101100011011001010111001100100000"),
        # Note: space_replacement option is not tested via API here as it's only used in direct func call
    ],
)
@pytest.mark.asyncio
async def test_text_to_binary_api(client: TestClient, input_text: str, include_spaces: bool, expected_binary: str):
    """Test the text_to_binary API endpoint."""
    payload = TextBinaryInput(
        text=input_text,
        mode="text_to_binary",
        include_spaces=include_spaces,
        space_replacement="00100000",  # Add default even if not directly used by API logic shown
    )
    response = client.post("/api/text-binary/", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = TextBinaryOutput(**response.json())

    assert output.original == input_text
    assert output.result == expected_binary
    assert output.mode == "text_to_binary"
    # Validate char mapping if needed
    if input_text and output.char_mapping:
        assert all(c in output.char_mapping for c in input_text)
        assert all(v in expected_binary for v in output.char_mapping.values())


# --- Test Binary to Text Conversion ---


@pytest.mark.parametrize(
    "input_binary, expected_text",
    [
        (BINARY_EXPECTED_SPACES, TEXT_INPUT),
        (BINARY_EXPECTED_NOSPACES, TEXT_INPUT),
        ("01000001", "A"),
        ("00100000 01110011 01110000 01100001 01100011 01100101 01110011 00100000", " spaces "),
        ("0010000001110011011100000110000101100011011001010111001100100000", " spaces "),
    ],
)
@pytest.mark.asyncio
async def test_binary_to_text_api(client: TestClient, input_binary: str, expected_text: str):
    """Test the binary_to_text API endpoint."""
    # Binary to text doesn't use include_spaces or space_replacement in API payload
    # Explicitly create dict without them to satisfy linter
    payload_dict = {"text": input_binary, "mode": "binary_to_text"}
    # payload = TextBinaryInput(text=input_binary, mode="binary_to_text")
    # response = client.post("/api/text-binary/", json=payload.dict(exclude_unset=True))
    response = client.post("/api/text-binary/", json=payload_dict)

    assert response.status_code == status.HTTP_200_OK
    output = TextBinaryOutput(**response.json())

    assert output.original == input_binary
    assert output.result == expected_text
    assert output.mode == "binary_to_text"
    # Validate char mapping if needed
    if input_binary and output.char_mapping:
        # Recreate chunks accurately for checking keys
        clean_binary = input_binary.replace(" ", "")
        binary_chunks = [clean_binary[i : i + 8] for i in range(0, len(clean_binary), 8)]
        assert all(chunk in output.char_mapping for chunk in binary_chunks)
        assert all(c in expected_text for c in output.char_mapping.values())


# --- Test Error Cases ---


@pytest.mark.parametrize(
    "input_text, mode, expected_status, error_substring",
    [
        ("", "text_to_binary", status.HTTP_400_BAD_REQUEST, "Input text cannot be empty"),
        (" ", "text_to_binary", status.HTTP_400_BAD_REQUEST, "Input text cannot be empty"),  # Trimmed is empty
        ("abc", "invalid_mode", status.HTTP_400_BAD_REQUEST, "Invalid conversion mode"),
        # Binary to text errors
        ("0100100", "binary_to_text", status.HTTP_400_BAD_REQUEST, "Binary length must be a multiple of 8"),
        ("01001000 123", "binary_to_text", status.HTTP_400_BAD_REQUEST, "Invalid binary input"),
        ("01001000 abcdefgh", "binary_to_text", status.HTTP_400_BAD_REQUEST, "Invalid binary input"),
        # Pydantic validation (e.g., missing mode)
        ("Test", None, status.HTTP_422_UNPROCESSABLE_ENTITY, "field required"),
    ],
)
@pytest.mark.asyncio
async def test_text_binary_errors(
    client: TestClient, input_text: str, mode: str | None, expected_status: int, error_substring: str
):
    """Test various error conditions for the text/binary converter."""
    payload_dict = {"text": input_text, "mode": mode}
    if mode is None:
        payload_dict.pop("mode")  # Test Pydantic missing field

    response = client.post("/api/text-binary/", json=payload_dict)

    assert response.status_code == expected_status
    if expected_status == status.HTTP_422_UNPROCESSABLE_ENTITY:
        assert error_substring in str(response.json()).lower()
    else:
        assert error_substring in response.json()["detail"]
