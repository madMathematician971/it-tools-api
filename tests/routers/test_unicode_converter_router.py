import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from pydantic import ValidationError

# from models.unicode_converter_models import UnicodeInput, UnicodeOutput # Incorrect import
# Import models from router file
from routers.unicode_converter_router import UnicodeInput, UnicodeOutput
from routers.unicode_converter_router import router as unicode_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(unicode_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Text to Unicode Encoding ---


@pytest.mark.parametrize(
    "input_text, prefix, separator, base, expected_result",
    [
        # Basic ASCII - Hex (Default)
        ("A", "U+", " ", 16, "U+0041"),
        ("Hi", "U+", " ", 16, "U+0048 U+0069"),
        # Basic ASCII - Decimal
        ("A", "", " ", 10, "65"),
        ("Hi", "", " ", 10, "72 105"),
        # Different Prefix/Separator - Hex
        ("A", "\\u", "", 16, "\\u0041"),
        ("Hi", "0x", ";", 16, "0x0048;0x0069"),
        # Different Base
        ("A", "", " ", 2, "1000001"),  # Binary
        ("Hi", "", " ", 8, "110 151"),  # Octal
        # Unicode characters
        ("€", "U+", " ", 16, "U+20AC"),
        ("你好", "U+", " ", 16, "U+4F60 U+597D"),
        ("你好", "", " ", 10, "20320 22909"),
        # Mixed
        ("A€", "U+", " ", 16, "U+0041 U+20AC"),
        # Empty string
        ("", "U+", " ", 16, ""),
    ],
)
@pytest.mark.asyncio
async def test_text_to_unicode_success(
    client: TestClient, input_text: str, prefix: str, separator: str, base: int, expected_result: str
):
    """Test successful encoding of text to Unicode code points."""
    payload = UnicodeInput(text=input_text, prefix=prefix, separator=separator, base=base)
    response = client.post("/api/unicode-converter/encode", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = UnicodeOutput(**response.json())
    assert output.result == expected_result


# --- Test Unicode to Text Decoding ---


@pytest.mark.parametrize(
    "input_codes, prefix, separator, base, expected_text",
    [
        # Basic ASCII - Hex (Default)
        ("U+0041", "U+", " ", 16, "A"),
        ("U+0048 U+0069", "U+", " ", 16, "Hi"),
        ("U+0048U+0069", "U+", "", 16, "Hi"),  # No separator
        # Basic ASCII - Decimal
        ("65", "", " ", 10, "A"),
        ("72 105", "", " ", 10, "Hi"),
        # Different Prefix/Separator - Hex
        ("\\u0041", "\\u", "", 16, "A"),
        ("0x0048;0x0069", "0x", ";", 16, "Hi"),
        # Different Base
        ("1000001", "", " ", 2, "A"),  # Binary
        ("110 151", "", " ", 8, "Hi"),  # Octal
        # Unicode characters
        ("U+20AC", "U+", " ", 16, "€"),
        ("U+4F60 U+597D", "U+", " ", 16, "你好"),
        ("20320 22909", "", " ", 10, "你好"),
        # Mixed
        ("U+0041 U+20AC", "U+", " ", 16, "A€"),
        # Hex without padding
        ("U+41 U+69", "U+", " ", 16, "Ai"),
        # Empty string
        ("", "U+", " ", 16, ""),
        # Separators only
        (" ; ; ", "U+", ";", 16, ""),
    ],
)
@pytest.mark.asyncio
async def test_unicode_to_text_success(
    client: TestClient, input_codes: str, prefix: str, separator: str, base: int, expected_text: str
):
    """Test successful decoding of Unicode code points string to text."""
    payload = UnicodeInput(text=input_codes, prefix=prefix, separator=separator, base=base)
    response = client.post("/api/unicode-converter/decode", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = UnicodeOutput(**response.json())
    assert output.result == expected_text


# --- Test Error Cases ---


@pytest.mark.parametrize(
    "endpoint, input_text, prefix, separator, base, expected_status, error_substring",
    [
        # Invalid Base for Pydantic
        (
            "encode",
            "A",
            "U+",
            " ",
            1,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Input should be greater than or equal to 2",
        ),
        (
            "encode",
            "A",
            "U+",
            " ",
            37,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Input should be less than or equal to 36",
        ),
        # Decode errors
        ("decode", "U+ABCX", "U+", " ", 16, status.HTTP_400_BAD_REQUEST, "Invalid code point value 'ABCX' for base 16"),
        ("decode", "102", "", " ", 2, status.HTTP_400_BAD_REQUEST, "Invalid code point value '102' for base 2"),
        (
            "decode",
            "U+110000",
            "U+",
            " ",
            16,
            status.HTTP_400_BAD_REQUEST,
            "Invalid code point value '110000' for base 16",
        ),  # Outside Unicode range
        ("decode", "ZZZ", "", " ", 10, status.HTTP_400_BAD_REQUEST, "Invalid code point value 'ZZZ' for base 10"),
        # Ambiguous case: prefix expected but missing (currently skipped in impl, leads to empty result)
        ("decode", "0041", "U+", " ", 16, status.HTTP_200_OK, None),  # Expect empty result, not error
    ],
)
@pytest.mark.asyncio
async def test_unicode_converter_errors(
    client: TestClient,
    endpoint: str,
    input_text: str,
    prefix: str,
    separator: str,
    base: int,
    expected_status: int,
    error_substring: str | None,
):
    """Test error handling for both encode and decode endpoints."""
    # If expecting a 422 due to base, test Pydantic validation directly
    if (
        expected_status == status.HTTP_422_UNPROCESSABLE_ENTITY
        and error_substring is not None
        and ("greater than or equal to 2" in error_substring or "less than or equal to 36" in error_substring)
    ):
        with pytest.raises(ValidationError) as excinfo:
            UnicodeInput(text=input_text, prefix=prefix, separator=separator, base=base)
        # Ensure error_substring is not None before assertion
        assert error_substring is not None
        # Compare lowercased strings for robustness
        assert error_substring.lower() in str(excinfo.value).lower()
        return  # Skip API call for these cases

    payload = UnicodeInput(text=input_text, prefix=prefix, separator=separator, base=base)
    response = client.post(f"/api/unicode-converter/{endpoint}", json=payload.model_dump())

    assert response.status_code == expected_status
    if expected_status == status.HTTP_422_UNPROCESSABLE_ENTITY:
        assert error_substring is not None
        assert error_substring in str(response.json()).lower()
    elif expected_status == status.HTTP_400_BAD_REQUEST:
        assert error_substring is not None
        assert error_substring.lower() in response.json()["detail"].lower()
    elif expected_status == status.HTTP_200_OK and error_substring is None:  # Special case for missing prefix
        output = UnicodeOutput(**response.json())
        assert output.result == ""
    else:
        pytest.fail(f"Unexpected status code {expected_status} or error condition")
