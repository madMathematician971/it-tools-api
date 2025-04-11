import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.base_converter_models import BaseConvertInput, BaseConvertOutput
from routers.base_converter_router import router as base_converter_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(base_converter_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Base Conversion ---


@pytest.mark.parametrize(
    "number_string, input_base, output_base, expected_result",
    [
        ("10", 10, 2, "1010"),  # Decimal to Binary
        ("1010", 2, 10, "10"),  # Binary to Decimal
        ("FF", 16, 10, "255"),  # Hex to Decimal
        ("255", 10, 16, "ff"),  # Decimal to Hex (lowercase output)
        ("777", 8, 10, "511"),  # Octal to Decimal
        ("511", 10, 8, "777"),  # Decimal to Octal
        ("10", 10, 36, "a"),  # Decimal to Base 36
        ("a", 36, 10, "10"),  # Base 36 to Decimal
        ("z", 36, 10, "35"),  # Base 36 (max digit) to Decimal
        ("35", 10, 36, "z"),  # Decimal to Base 36 (max digit)
        ("1A", 16, 2, "11010"),  # Hex to Binary
        ("11010", 2, 16, "1a"),  # Binary to Hex
        ("0", 10, 16, "0"),  # Zero conversion
        ("-10", 10, 2, "-1010"),  # Negative Decimal to Binary
        ("-1010", 2, 10, "-10"),  # Negative Binary to Decimal
        ("-FF", 16, 10, "-255"),  # Negative Hex to Decimal
        ("-255", 10, 16, "-ff"),  # Negative Decimal to Hex
    ],
)
@pytest.mark.asyncio
async def test_base_convert_success(
    client: TestClient, number_string: str, input_base: int, output_base: int, expected_result: str
):
    """Test successful base conversions."""
    payload = BaseConvertInput(number_string=number_string, input_base=input_base, output_base=output_base)
    response = client.post("/api/base/convert", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = BaseConvertOutput(**response.json())
    assert output.result_string == expected_result
    assert output.input_number_string == number_string
    assert output.input_base == input_base
    assert output.output_base == output_base


@pytest.mark.parametrize(
    "number_string, input_base, output_base, expected_error_detail",
    [
        ("12", 2, 10, "Invalid input: invalid literal for int() with base 2: '12'"),  # Invalid digit for base
        ("G", 16, 10, "Invalid input: invalid literal for int() with base 16: 'G'"),  # Invalid hex digit
        ("", 10, 16, "Invalid input: invalid literal for int() with base 10: ''"),  # Empty string
        ("AF.B", 16, 10, "Invalid input: invalid literal for int() with base 16: 'AF.B'"),  # Non-integer input
    ],
)
@pytest.mark.asyncio
async def test_base_convert_invalid_input(
    client: TestClient, number_string: str, input_base: int, output_base: int, expected_error_detail: str
):
    """Test base conversions with invalid inputs."""
    payload = BaseConvertInput(number_string=number_string, input_base=input_base, output_base=output_base)
    response = client.post("/api/base/convert", json=payload.model_dump())

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == expected_error_detail
