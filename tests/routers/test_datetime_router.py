from datetime import datetime

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from freezegun import freeze_time

from models.datetime_models import DateTimeConvertInput, DateTimeConvertOutput
from routers.datetime_router import router as datetime_router

# Fixed point in time for consistent results
FROZEN_TIME = "2023-10-27T10:30:45.123Z"  # ISO 8601 UTC
FROZEN_DT_UTC = datetime.fromisoformat(FROZEN_TIME.replace("Z", "+00:00"))
# Use float for timestamps to preserve precision
FROZEN_UNIX_S_FLOAT = FROZEN_DT_UTC.timestamp()
FROZEN_UNIX_MS_FLOAT = FROZEN_DT_UTC.timestamp() * 1000.0
# Integer versions might still be needed for some input tests
FROZEN_UNIX_S_INT = int(FROZEN_UNIX_S_FLOAT)
FROZEN_UNIX_MS_INT = int(FROZEN_UNIX_MS_FLOAT)


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(datetime_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test DateTime Conversion Success ---
@freeze_time(FROZEN_TIME)
@pytest.mark.parametrize(
    "input_value, input_format, output_format, expected_result",
    [
        # Unix Seconds (Float input/output) -> Various
        (FROZEN_UNIX_S_FLOAT, "unix_s", "iso8601", "2023-10-27T10:30:45.123000Z"),  # Expect microseconds
        (FROZEN_UNIX_S_FLOAT, "unix_s", "unix_ms", FROZEN_UNIX_MS_FLOAT),
        (FROZEN_UNIX_S_FLOAT, "unix_s", "rfc2822", "Fri, 27 Oct 2023 10:30:45 GMT"),  # Expect GMT
        (FROZEN_UNIX_S_FLOAT, "unix_s", "human_readable", "Friday, October 27, 2023 at 10:30:45 AM UTC"),  # Expect UTC
        (FROZEN_UNIX_S_FLOAT, "unix_s", "custom:%Y-%m-%d %H:%M", "2023-10-27 10:30"),
        # Unix Milliseconds (Float input/output) -> Various
        (FROZEN_UNIX_MS_FLOAT, "unix_ms", "iso8601", "2023-10-27T10:30:45.123000Z"),
        (FROZEN_UNIX_MS_FLOAT, "unix_ms", "unix_s", FROZEN_UNIX_S_FLOAT),
        (FROZEN_UNIX_MS_FLOAT, "unix_ms", "custom:%H:%M:%S.%f", "10:30:45.123000"),
        # ISO 8601 -> Various (Outputting float timestamps)
        (FROZEN_TIME, "iso8601", "unix_s", FROZEN_UNIX_S_FLOAT),
        (FROZEN_TIME, "iso8601", "unix_ms", FROZEN_UNIX_MS_FLOAT),
        ("2023-10-27T12:30:45.123+02:00", "iso8601", "iso8601", "2023-10-27T10:30:45.123000Z"),  # With offset
        ("2023-10-27 10:30:45.123", "iso8601", "iso8601", "2023-10-27T10:30:45.123000Z"),  # Assumed UTC
        # Auto -> Various (using frozen time values, expecting float timestamps)
        (FROZEN_UNIX_S_FLOAT, "auto", "iso8601", "2023-10-27T10:30:45.123000Z"),
        (FROZEN_UNIX_MS_FLOAT, "auto", "iso8601", "2023-10-27T10:30:45.123000Z"),
        (str(FROZEN_UNIX_S_FLOAT), "auto", "iso8601", "2023-10-27T10:30:45.123000Z"),  # Numeric string (unix_s)
        (str(FROZEN_UNIX_MS_FLOAT), "auto", "iso8601", "2023-10-27T10:30:45.123000Z"),  # Numeric string (unix_ms)
        (FROZEN_TIME, "auto", "unix_s", FROZEN_UNIX_S_FLOAT),
        # Date string without ms - timestamp will lose precision
        ("2023-10-27 10:30:45", "auto", "unix_s", float(FROZEN_UNIX_S_INT)),
        ("October 27, 2023 10:30:45.123 AM UTC", "auto", "iso8601", "2023-10-27T10:30:45.123000Z"),
        (
            "Fri, 27 Oct 2023 10:30:45 GMT",
            "auto",
            "iso8601",
            "2023-10-27T10:30:45.000000Z",
        ),  # dateutil parses GMT as +00:00, loses ms?
        # Custom Format Output
        (FROZEN_TIME, "iso8601", "custom:%A %d %b %Y", "Friday 27 Oct 2023"),
        (FROZEN_TIME, "iso8601", "custom:%H-%M", "10-30"),
    ],
)
@pytest.mark.asyncio
async def test_datetime_convert_success(
    client: TestClient, input_value, input_format: str, output_format: str, expected_result
):
    """Test successful datetime conversions between various formats."""
    payload = DateTimeConvertInput(input_value=input_value, input_format=input_format, output_format=output_format)
    response = client.post("/api/datetime/convert", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = DateTimeConvertOutput(**response.json())
    # Allow for small float differences in timestamp comparisons
    if isinstance(expected_result, float):
        assert isinstance(output.result, float)
        assert abs(output.result - expected_result) < 0.001  # Tolerate tiny float diff
    else:
        assert output.result == expected_result
    # Check parsed_utc_iso includes microseconds and Z suffix
    assert output.parsed_utc_iso is not None
    assert output.parsed_utc_iso.endswith("Z")
    assert "." in output.parsed_utc_iso


# --- Test DateTime Conversion Invalid Inputs (Expecting API 400 Error) ---
@freeze_time(FROZEN_TIME)
@pytest.mark.parametrize(
    "input_value, input_format, output_format, error_substring",
    [
        # Invalid input values for the specified format
        ("not a date", "iso8601", "unix_s", "Invalid input or format:"),
        ("invalid", "auto", "unix_s", "Could not automatically parse string input"),
        (FROZEN_TIME, "unix_s", "iso8601", "unix_s input must be a number."),
        (12345, "iso8601", "unix_s", "iso8601 input must be a string."),
        # Invalid input/output formats
        (FROZEN_UNIX_S_FLOAT, "invalid_format", "unix_ms", "Unsupported input_format"),
        (FROZEN_UNIX_S_FLOAT, "unix_s", "invalid_output", "Unsupported output_format"),
    ],
)
@pytest.mark.asyncio
async def test_datetime_convert_api_errors(
    client: TestClient, input_value, input_format, output_format, error_substring
):
    """Test cases where the API should return a 400 Bad Request."""
    payload = DateTimeConvertInput(input_value=input_value, input_format=input_format, output_format=output_format)
    response = client.post("/api/datetime/convert", json=payload.model_dump())
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = response.json()
    assert "detail" in response_data
    # Check specific error raised by the router's ValueError handlers
    assert error_substring.lower() in response_data["detail"].lower()


# --- Test DateTime Conversion Invalid Input Types (Expecting Pydantic 422 Error) ---
@freeze_time(FROZEN_TIME)
@pytest.mark.parametrize(
    "input_value, input_format, output_format, error_detail_field",
    [
        # Test cases for invalid input types that Pydantic should catch
        (None, "iso8601", "unix_s", ["input_value"]),  # None is not str/int/float
        ([], "iso8601", "unix_s", ["input_value"]),  # List is not str/int/float
        ({}, "auto", "iso8601", ["input_value"]),  # Dict is not str/int/float
    ],
)
@pytest.mark.asyncio
async def test_datetime_convert_pydantic_errors(
    client: TestClient, input_value, input_format, output_format, error_detail_field
):
    """Test cases where Pydantic validation should raise a 422 Unprocessable Entity."""
    # Pydantic validation happens implicitly when creating the model or by FastAPI
    # We expect a 422 status code directly from the client call
    response = client.post(
        "/api/datetime/convert",
        json={"input_value": input_value, "input_format": input_format, "output_format": output_format},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data
    assert isinstance(response_data["detail"], list)
    # Check that the expected error location and message substring exist in the Pydantic error details
    found_error = False
    # Pydantic V2 provides separate errors for Union types, loc might be more specific
    # e.g., ['body', 'input_value', 'str'] instead of just ['body', 'input_value']
    expected_loc_prefix = ["body", error_detail_field[0]]
    expected_msgs = [
        "Input should be a valid string",
        "Input should be a valid integer",
        "Input should be a valid number",  # Pydantic uses 'number' for float
    ]
    for error in response_data["detail"]:
        actual_loc = error.get("loc", [])
        actual_msg = error.get("msg", "")
        # Check if the actual location starts with the expected prefix
        loc_match = actual_loc[: len(expected_loc_prefix)] == expected_loc_prefix
        # Check if the actual error message contains any of the expected type error messages (case-insensitive)
        msg_match = any(expected_msg.lower() in actual_msg.lower() for expected_msg in expected_msgs)
        if loc_match and msg_match:
            found_error = True
            break
    assert (
        found_error
    ), f"Expected Pydantic error for field '{error_detail_field[0]}' with one of msg containing {expected_msgs} not found. Got: {response_data['detail']}"
