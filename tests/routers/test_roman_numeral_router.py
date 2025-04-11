import re  # !pylint: disable=unused-import
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
    # If not a string, it's likely an error case where input_value might be set differently
    # The error check below should cover those scenarios
    assert output.error is None


@pytest.mark.parametrize(
    "invalid_roman, error_substring, expected_status",
    [
        ("IIII", "not in standard form", status.HTTP_200_OK),
        ("VV", "not in standard form", status.HTTP_200_OK),
        ("IM", "not in standard form", status.HTTP_200_OK),
        ("VX", "not in standard form", status.HTTP_200_OK),
        ("MMMM", "Input should be less than or equal to 3999", status.HTTP_200_OK),
        ("ABC", "Invalid characters in Roman numeral", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("", "Invalid characters in Roman numeral", status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
)
@pytest.mark.asyncio
async def test_decode_from_roman_invalid_input(
    client: TestClient, invalid_roman: str, error_substring: str, expected_status: int
):
    """Test decoding with invalid Roman numeral strings."""
    payload_dict = {"roman_numeral": invalid_roman}
    response = client.post("/api/roman-numerals/decode", json=payload_dict)

    assert response.status_code == expected_status

    if expected_status == status.HTTP_422_UNPROCESSABLE_ENTITY:
        assert error_substring.lower() in str(response.json()).lower()
    elif expected_status == status.HTTP_200_OK:
        output = RomanOutput(**response.json())
        assert output.result == 0
        assert output.error is not None
        assert error_substring.lower() in output.error.lower()
    else:
        pytest.fail(f"Unexpected status code in test parameterization: {expected_status}")
