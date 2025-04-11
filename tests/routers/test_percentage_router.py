import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.percentage_models import PercentageCalcType, PercentageInput, PercentageOutput
from routers.percentage_router import router as percentage_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(percentage_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Percentage Calculations ---


@pytest.mark.parametrize(
    "value1, value2, calc_type, expected_result, expected_desc_substrings",
    [
        # percent_of: v1% of v2
        (10, 100, PercentageCalcType.percent_of, 10.0, ["10.0% of 100.0 is 10.0"]),
        (25, 200, PercentageCalcType.percent_of, 50.0, ["25.0% of 200.0 is 50.0"]),
        (50, 10, PercentageCalcType.percent_of, 5.0, ["50.0% of 10.0 is 5.0"]),
        (0, 100, PercentageCalcType.percent_of, 0.0, ["0.0% of 100.0 is 0.0"]),
        (150, 100, PercentageCalcType.percent_of, 150.0, ["150.0% of 100.0 is 150.0"]),
        (10, -50, PercentageCalcType.percent_of, -5.0, ["10.0% of -50.0 is -5.0"]),
        # x_is_what_percent_of_y: v1 is what % of v2?
        (10, 100, PercentageCalcType.x_is_what_percent_of_y, 10.0, ["10.0 is 10.00% of 100.0"]),
        (50, 200, PercentageCalcType.x_is_what_percent_of_y, 25.0, ["50.0 is 25.00% of 200.0"]),
        (5, 10, PercentageCalcType.x_is_what_percent_of_y, 50.0, ["5.0 is 50.00% of 10.0"]),
        (0, 100, PercentageCalcType.x_is_what_percent_of_y, 0.0, ["0.0 is 0.00% of 100.0"]),
        (150, 100, PercentageCalcType.x_is_what_percent_of_y, 150.0, ["150.0 is 150.00% of 100.0"]),
        (-5, 50, PercentageCalcType.x_is_what_percent_of_y, -10.0, ["-5.0 is -10.00% of 50.0"]),
        (10, -50, PercentageCalcType.x_is_what_percent_of_y, -20.0, ["10.0 is -20.00% of -50.0"]),
        # percent_increase: % increase from v1 to v2
        (100, 110, PercentageCalcType.percent_increase, 10.0, ["Increase from 100.0 to 110.0 is 10.00%"]),
        (50, 100, PercentageCalcType.percent_increase, 100.0, ["Increase from 50.0 to 100.0 is 100.00%"]),
        (10, 10, PercentageCalcType.percent_increase, 0.0, ["Increase from 10.0 to 10.0 is 0.00%"]),
        (
            100,
            50,
            PercentageCalcType.percent_increase,
            -50.0,
            ["Increase from 100.0 to 50.0 is -50.00%"],
        ),
        (-100, -50, PercentageCalcType.percent_increase, 50.0, ["Increase from -100.0 to -50.0 is 50.00%"]),
        (-50, -100, PercentageCalcType.percent_increase, -100.0, ["Increase from -50.0 to -100.0 is -100.00%"]),
        # percent_decrease: % decrease from v1 to v2
        (100, 90, PercentageCalcType.percent_decrease, 10.0, ["Decrease from 100.0 to 90.0 is 10.00%"]),
        (100, 50, PercentageCalcType.percent_decrease, 50.0, ["Decrease from 100.0 to 50.0 is 50.00%"]),
        (10, 10, PercentageCalcType.percent_decrease, 0.0, ["Decrease from 10.0 to 10.0 is 0.00%"]),
        (
            50,
            100,
            PercentageCalcType.percent_decrease,
            -100.0,
            ["Decrease from 50.0 to 100.0 is -100.00%"],
        ),
        (-50, -100, PercentageCalcType.percent_decrease, 100.0, ["Decrease from -50.0 to -100.0 is 100.00%"]),
        (-100, -50, PercentageCalcType.percent_decrease, -50.0, ["Decrease from -100.0 to -50.0 is -50.00%"]),
    ],
)
@pytest.mark.asyncio
async def test_percentage_calculate_success(
    client: TestClient,
    value1: float,
    value2: float,
    calc_type: PercentageCalcType,
    expected_result: float,
    expected_desc_substrings: list[str],
):
    """Test successful percentage calculations for all types."""
    payload = PercentageInput(value1=value1, value2=value2, calc_type=calc_type)
    response = client.post("/api/percentage/calculate", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = PercentageOutput(**response.json())

    assert output.error is None
    assert output.result == pytest.approx(expected_result)  # Use approx for float comparison
    assert isinstance(output.calculation_description, str)
    for sub in expected_desc_substrings:
        assert sub in output.calculation_description


@pytest.mark.parametrize(
    "value1, value2, calc_type, error_substring",
    [
        # Division by zero errors
        (10, 0, PercentageCalcType.x_is_what_percent_of_y, "Cannot calculate percentage of zero."),
        (0, 0, PercentageCalcType.x_is_what_percent_of_y, "Cannot calculate percentage of zero."),
        (0, 10, PercentageCalcType.percent_increase, "Cannot calculate percentage increase from zero."),
        (0, 10, PercentageCalcType.percent_decrease, "Cannot calculate percentage decrease from zero."),
        # Invalid calc_type (should be caught by Pydantic but test API response)
        (10, 100, "invalid_type", "Invalid calculation type specified."),
    ],
)
@pytest.mark.asyncio
async def test_percentage_calculate_errors(
    client: TestClient, value1: float, value2: float, calc_type: str | PercentageCalcType, error_substring: str
):
    """Test percentage calculations that result in errors (division by zero, invalid type)."""
    # Use dict to allow invalid enum value for testing
    payload_dict = {"value1": value1, "value2": value2, "calc_type": calc_type}
    response = client.post("/api/percentage/calculate", json=payload_dict)

    # Division by zero errors result in 200 OK with error in body
    if isinstance(calc_type, PercentageCalcType) and (
        (value2 == 0 and calc_type == PercentageCalcType.x_is_what_percent_of_y)
        or (value1 == 0 and calc_type == PercentageCalcType.percent_increase)
        or (value1 == 0 and calc_type == PercentageCalcType.percent_decrease)
    ):
        assert response.status_code == status.HTTP_200_OK
        output = PercentageOutput(**response.json())
        assert output.result is None
        assert output.error is not None
        assert error_substring.lower() in output.error.lower()
    # Invalid calc_type results in 422 from Pydantic validation
    elif calc_type == "invalid_type":
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        expected_pydantic_error = (
            "Input should be 'percent_of', 'x_is_what_percent_of_y', 'percent_increase' or 'percent_decrease'"
        )
        assert expected_pydantic_error.lower() in str(response.json()).lower()
    else:
        # This case should ideally not be hit if parameterization is correct
        pytest.fail(
            f"Unhandled case in test_percentage_calculate_errors: val1={value1}, val2={value2}, type={calc_type}"
        )
