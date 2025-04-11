import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.temperature_models import TemperatureInput, TemperatureOutput, TemperatureUnit
from routers.temperature_router import router as temperature_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(temperature_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Temperature Conversion ---


@pytest.mark.parametrize(
    "value, unit, expected_c, expected_f, expected_k",
    [
        # Celsius input
        (0, TemperatureUnit.celsius, 0.0, 32.0, 273.15),
        (100, TemperatureUnit.celsius, 100.0, 212.0, 373.15),
        (-40, TemperatureUnit.celsius, -40.0, -40.0, 233.15),
        (25.5, TemperatureUnit.celsius, 25.5, 77.9, 298.65),
        # Fahrenheit input
        (32, TemperatureUnit.fahrenheit, 0.0, 32.0, 273.15),
        (212, TemperatureUnit.fahrenheit, 100.0, 212.0, 373.15),
        (-40, TemperatureUnit.fahrenheit, -40.0, -40.0, 233.15),
        (77.9, TemperatureUnit.fahrenheit, 25.5, 77.9, 298.65),
        # Kelvin input
        (273.15, TemperatureUnit.kelvin, 0.0, 32.0, 273.15),
        (373.15, TemperatureUnit.kelvin, 100.0, 212.0, 373.15),
        (0, TemperatureUnit.kelvin, -273.15, -459.67, 0.0),  # Absolute zero
        (298.65, TemperatureUnit.kelvin, 25.5, 77.9, 298.65),
    ],
)
@pytest.mark.asyncio
async def test_convert_temperature_success(
    client: TestClient, value: float, unit: TemperatureUnit, expected_c: float, expected_f: float, expected_k: float
):
    """Test successful temperature conversions between C, F, and K."""
    payload = TemperatureInput(value=value, unit=unit)
    response = client.post("/api/temperature/convert", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = TemperatureOutput(**response.json())

    assert output.error is None
    # Use pytest.approx for floating point comparisons
    assert output.celsius == pytest.approx(expected_c, abs=0.01)
    assert output.fahrenheit == pytest.approx(expected_f, abs=0.01)
    assert output.kelvin == pytest.approx(expected_k, abs=0.01)


@pytest.mark.asyncio
async def test_convert_temperature_below_absolute_zero(client: TestClient):
    """Test conversion attempt with Kelvin value below absolute zero."""
    payload = TemperatureInput(value=-10, unit=TemperatureUnit.kelvin)
    response = client.post("/api/temperature/convert", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK  # API returns 200 OK with error
    output = TemperatureOutput(**response.json())
    assert output.error is not None
    assert "Kelvin cannot be below absolute zero" in output.error
    # Check that other values might be zeroed or default
    assert output.celsius == 0
    assert output.fahrenheit == 0
    assert output.kelvin == -10  # Original invalid Kelvin might be returned


# Test invalid enum value (should be caught by Pydantic)
@pytest.mark.asyncio
async def test_convert_temperature_invalid_unit(client: TestClient):
    """Test conversion with an invalid temperature unit."""
    response = client.post("/api/temperature/convert", json={"value": 20, "unit": "Rankine"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Update substring and use case-insensitive check
    expected_error_substring = "Input should be 'celsius', 'fahrenheit' or 'kelvin'"
    assert expected_error_substring.lower() in str(response.json()).lower()
