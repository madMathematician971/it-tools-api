import datetime

import pytest
import ulid  # Import the module directly
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from freezegun import freeze_time

from models.ulid_models import UlidResponse
from routers.ulid_router import router as ulid_router

# Fixed time for consistent ULID generation
FROZEN_TIME = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
FROZEN_TIME_STR = FROZEN_TIME.isoformat()


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(ulid_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test ULID Generation ---


@freeze_time(FROZEN_TIME_STR)
@pytest.mark.asyncio
async def test_generate_ulid_current_time(client: TestClient):
    """Test generating a ULID using the current time (frozen)."""
    response = client.get("/api/ulid/")

    assert response.status_code == status.HTTP_200_OK
    output = UlidResponse(**response.json())

    # Validate ULID format
    assert len(output.ulid) == 26
    try:
        # Use ulid.parse() for parsing
        parsed_ulid = ulid.parse(output.ulid)
    except ValueError:
        pytest.fail(f"Generated ULID {output.ulid} is not valid.")

    # Validate timestamp component matches frozen time
    assert parsed_ulid.timestamp().datetime == FROZEN_TIME

    # Validate other fields using the response model
    expected_iso_str = FROZEN_TIME.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    assert output.timestamp == expected_iso_str
    assert output.timestamp_ms == int(FROZEN_TIME.timestamp() * 1000)
    # Compare response randomness (hex str) with parsed randomness (bytes -> hex str)
    assert output.randomness == parsed_ulid.bytes[6:].hex()


@pytest.mark.asyncio
async def test_generate_ulid_specific_timestamp(client: TestClient):
    """Test generating a ULID using a specific provided timestamp."""
    test_timestamp_sec = 1609459200.500  # 2021-01-01 00:00:00.500 UTC
    expected_dt = datetime.datetime.fromtimestamp(test_timestamp_sec, tz=datetime.timezone.utc)
    expected_iso = expected_dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    expected_ms = int(test_timestamp_sec * 1000)

    response = client.get(f"/api/ulid/?timestamp={test_timestamp_sec}")

    assert response.status_code == status.HTTP_200_OK
    output = UlidResponse(**response.json())

    # Validate ULID format
    assert len(output.ulid) == 26
    try:
        # Use ulid.parse() for parsing
        parsed_ulid = ulid.parse(output.ulid)
    except ValueError:
        pytest.fail(f"Generated ULID {output.ulid} is not valid.")

    # Validate timestamp component matches provided timestamp
    ulid_timestamp_ms = int(parsed_ulid.timestamp().timestamp * 1000)
    assert ulid_timestamp_ms == expected_ms

    # Validate other fields using the response model
    assert output.timestamp == expected_iso
    assert output.timestamp_ms == expected_ms
    # Compare response randomness (hex str) with parsed randomness (bytes -> hex str)
    assert output.randomness == parsed_ulid.bytes[6:].hex()

    # Check that the generated ULID indeed corresponds to the input timestamp
    # Use ulid.from_timestamp() directly
    ulid_from_ts = ulid.from_timestamp(expected_dt)  # Create base ULID from timestamp
    assert output.ulid.startswith(str(ulid_from_ts)[:10])  # Compare only the timestamp part


@pytest.mark.asyncio
async def test_generate_ulid_invalid_timestamp(client: TestClient):
    """Test ULID generation with an invalid timestamp format."""
    invalid_timestamp = "not-a-number"
    response = client.get(f"/api/ulid/?timestamp={invalid_timestamp}")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Update assertion for Pydantic v2 message
    assert "input should be a valid number" in str(response.json()).lower()
