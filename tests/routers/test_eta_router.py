from datetime import datetime, timezone

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

# Import models defined within the router file if they exist there,
# otherwise adjust path as necessary.
# Assuming they might be in a separate models file:
# from models.eta_models import EtaInput, EtaOutput
# If they are in the router file (as shown in context):
from routers.eta_router import EtaInput, EtaOutput
from routers.eta_router import router as eta_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(eta_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test ETA Calculation ---


@pytest.mark.parametrize(
    "start_time_iso, duration_seconds, expected_end_time_iso",
    [
        # Basic additions
        ("2023-10-27T10:00:00Z", 3600, "2023-10-27T11:00:00+00:00"),  # Add 1 hour (UTC)
        ("2023-10-27T12:00:00+02:00", 60, "2023-10-27T12:01:00+02:00"),  # Add 1 minute (with offset)
        ("2023-12-31T23:59:59Z", 1, "2024-01-01T00:00:00+00:00"),  # Cross year boundary
        ("2024-02-28T23:59:00Z", 120, "2024-02-29T00:01:00+00:00"),  # Cross leap day
        # Zero duration
        ("2023-11-15T08:30:00Z", 0, "2023-11-15T08:30:00+00:00"),
        # Large duration
        (
            "2023-01-01T00:00:00Z",
            86400 * 365,
            "2024-01-01T00:00:00+00:00",
        ),  # Add 1 year (approx, doesn't account for leap sec)
        # Timezone handling
        (
            "2023-10-27T10:00:00",
            3600,
            "2023-10-27T11:00:00+00:00",
        ),  # No TZ in input, should assume UTC and output with UTC
        ("2023-10-27T05:00:00-05:00", 7200, "2023-10-27T07:00:00-05:00"),  # Maintain input offset
    ],
)
@pytest.mark.asyncio
async def test_calculate_eta_success(
    client: TestClient, start_time_iso: str, duration_seconds: int, expected_end_time_iso: str
):
    """Test successful ETA calculations."""
    payload = EtaInput(start_time_iso=start_time_iso, duration_seconds=duration_seconds)
    response = client.post("/api/eta/calculate", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = EtaOutput(**response.json())

    # Parse expected and actual end times to compare datetime objects for accuracy
    try:
        expected_dt = datetime.fromisoformat(expected_end_time_iso)
        actual_dt = datetime.fromisoformat(output.end_time)
        # Compare timestamps for equality, ignoring potential minor format differences in iso string
        assert actual_dt.timestamp() == expected_dt.timestamp()
        assert output.duration_seconds == duration_seconds
        # Check if start_time in output matches input (potentially with added TZ info)
        start_dt_out = datetime.fromisoformat(output.start_time)
        start_dt_in_parsed = datetime.fromisoformat(start_time_iso)  # Parse input again for comparison
        if start_dt_in_parsed.tzinfo is None:
            start_dt_in_parsed = start_dt_in_parsed.replace(tzinfo=timezone.utc)
        assert start_dt_out.timestamp() == start_dt_in_parsed.timestamp()

    except ValueError as e:
        pytest.fail(f"Could not parse expected or actual ISO datetime strings: {e}")


@pytest.mark.parametrize(
    "start_time_iso, duration_seconds, expected_status, error_substring",
    [
        # Invalid ISO format - These are now accepted by fromisoformat, expect 200 OK
        # ("2023-10-27 10:00:00", 60, status.HTTP_400_BAD_REQUEST, "Invalid start_time_iso format"), # Now parses
        ("invalid date", 60, status.HTTP_400_BAD_REQUEST, "Invalid start_time_iso format"),
        # ("20231027T100000Z", 60, status.HTTP_400_BAD_REQUEST, "Invalid start_time_iso format"), # Now parses
        ("", 60, status.HTTP_400_BAD_REQUEST, "Invalid start_time_iso format"),
        # Invalid duration (negative)
        (
            "2023-10-27T10:00:00Z",
            -1,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Input should be greater than or equal to 0",
        ),
        # Invalid duration type
        ("2023-10-27T10:00:00Z", "sixty", status.HTTP_422_UNPROCESSABLE_ENTITY, "Input should be a valid integer"),
    ],
)
@pytest.mark.asyncio
async def test_calculate_eta_invalid_input(
    client: TestClient, start_time_iso: str, duration_seconds, expected_status: int, error_substring: str
):
    """Test ETA calculations with invalid inputs."""
    payload_dict = {"start_time_iso": start_time_iso, "duration_seconds": duration_seconds}
    response = client.post("/api/eta/calculate", json=payload_dict)

    assert response.status_code == expected_status

    # Check the detail message for the specific error
    response_data = response.json()
    assert "detail" in response_data
    if isinstance(response_data["detail"], list):
        # Pydantic v2 errors are lists of dicts
        error_found = False
        for error in response_data["detail"]:
            if error_substring in error.get("msg", ""):
                error_found = True
                break
        assert (
            error_found
        ), f"Expected error substring '{error_substring}' not found in details: {response_data['detail']}"
    else:
        # Handle older Pydantic or direct HTTPException string detail
        assert error_substring in response_data["detail"]
