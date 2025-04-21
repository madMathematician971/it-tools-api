import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.roman_numeral_models import RomanDecodeInput, RomanEncodeInput, RomanOutput
from routers.roman_numeral_router import router as roman_numeral_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(roman_numeral_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Roman Numeral Encoding ---


@pytest.mark.parametrize(
    "number, expected_roman",
    [
        (1, "I"),
        (4, "IV"),
        (5, "V"),
        (9, "IX"),
        (10, "X"),
        (42, "XLII"),
        (50, "L"),
        (99, "XCIX"),
        (100, "C"),
        (499, "CDXCIX"),
        (500, "D"),
        (999, "CMXCIX"),
        (1000, "M"),
        (1994, "MCMXCIV"),
        (3999, "MMMCMXCIX"),  # Max value
    ],
)
@pytest.mark.asyncio
async def test_encode_to_roman_success(client: TestClient, number: int, expected_roman: str):
    """Test successful encoding of integers to Roman numerals."""
    payload = RomanEncodeInput(number=number)
    response = client.post("/api/roman-numerals/encode", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = RomanOutput(**response.json())
    assert output.result == expected_roman
    assert output.input_value == number
    assert output.error is None


@pytest.mark.parametrize(
    "invalid_number, error_substring",
    [
        (0, "Input should be greater than or equal to 1"),
        (4000, "Input should be less than or equal to 3999"),
        (-10, "Input should be greater than or equal to 1"),
    ],
)
@pytest.mark.asyncio
async def test_encode_to_roman_invalid_input(client: TestClient, invalid_number: int, error_substring: str):
    """Test encoding with numbers outside the valid range (1-3999)."""
    payload = {"number": invalid_number}  # Use dict for Pydantic validation test
    response = client.post("/api/roman-numerals/encode", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert error_substring.lower() in str(response.json()).lower()


# --- Test Roman Numeral Decoding ---


@pytest.mark.parametrize(
    "roman_numeral, expected_number",
    [
        ("I", 1),
        ("IV", 4),
        ("V", 5),
        ("IX", 9),
        ("X", 10),
        ("XLII", 42),
        ("L", 50),
        ("XCIX", 99),
        ("C", 100),
        ("CDXCIX", 499),
        ("D", 500),
        ("CMXCIX", 999),
        ("M", 1000),
        ("MCMXCIV", 1994),
        ("MMMCMXCIX", 3999),
        # Lowercase input
        ("mcmxciv", 1994),
    ],
)
@pytest.mark.asyncio
async def test_decode_from_roman_success(client: TestClient, roman_numeral: str, expected_number: int):
    """Test successful decoding of Roman numerals to integers."""
    payload = RomanDecodeInput(roman_numeral=roman_numeral)
    response = client.post("/api/roman-numerals/decode", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = RomanOutput(**response.json())
    assert output.result == expected_number
    if isinstance(output.input_value, str):
        assert output.input_value.upper() == roman_numeral.upper()
    # Check that error is None for valid standard numerals
    assert output.error is None


@pytest.mark.parametrize(
    "invalid_roman, error_substring, expected_status",
    [
        # Non-standard forms return 400 with warning
        ("IIII", "Warning: Roman numeral is not in standard form.", status.HTTP_400_BAD_REQUEST),
        ("VV", "Warning: Roman numeral is not in standard form.", status.HTTP_400_BAD_REQUEST),
        ("IM", "Warning: Roman numeral is not in standard form.", status.HTTP_400_BAD_REQUEST),
        ("VX", "Warning: Roman numeral is not in standard form.", status.HTTP_400_BAD_REQUEST),
        ("MMMM", "Decoded value (4000) is outside the standard range (1-3999)", status.HTTP_400_BAD_REQUEST),
        # Invalid characters / empty caught by Pydantic validation (422)
        ("ABC", "Invalid characters in Roman numeral", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("", "Invalid characters in Roman numeral", status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
)
@pytest.mark.asyncio
async def test_decode_from_roman_invalid_input(
    client: TestClient, invalid_roman: str, error_substring: str, expected_status: int
):
    """Test decoding with invalid Roman numeral strings."""
    # Use dict to bypass Pydantic validation for cases testing endpoint logic (like non-standard)
    # For cases testing Pydantic (422), this doesn't strictly matter but is fine.
    payload_dict = {"roman_numeral": invalid_roman}
    response = client.post("/api/roman-numerals/decode", json=payload_dict)

    assert response.status_code == expected_status

    # Updated logic for 400 Bad Request vs 422 Unprocessable Entity
    if expected_status == status.HTTP_400_BAD_REQUEST:
        response_data = response.json()
        assert "detail" in response_data
        assert error_substring.lower() in response_data["detail"].lower()
    elif expected_status == status.HTTP_422_UNPROCESSABLE_ENTITY:
        # FastAPI/Pydantic validation error structure is different
        response_data = response.json()
        assert "detail" in response_data
        assert isinstance(response_data["detail"], list)
        assert len(response_data["detail"]) > 0
        # Check if expected substring is in any of the validation error messages
        found_error = False
        for error in response_data["detail"]:
            if error_substring.lower() in error.get("msg", "").lower():
                found_error = True
                break
        assert (
            found_error
        ), f"Expected error substring '{error_substring}' not found in 422 details: {response_data['detail']}"
    else:
        pytest.fail(f"Unexpected expected_status code in test parameterization: {expected_status}")
