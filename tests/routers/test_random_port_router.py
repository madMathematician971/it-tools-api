from typing import Optional

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from pydantic import BaseModel

from routers.random_port_router import COMMON_PORTS_TO_EXCLUDE, MAX_PORT, MIN_PORT, WELL_KNOWN_PORTS_MAX
from routers.random_port_router import router as random_port_router

# --- Helper Functions for Test --- (Assuming these might not exist elsewhere)


def _get_known_ports():
    # Simple placeholder - replace with actual logic if available
    return set(range(MIN_PORT, WELL_KNOWN_PORTS_MAX + 1))


def _get_common_ports():
    # Simple placeholder - replace with actual logic if available
    return COMMON_PORTS_TO_EXCLUDE


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(random_port_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Random Port Generation (/generate) ---


@pytest.mark.parametrize(
    "count, min_p, max_p, exclude_wk, exclude_cmn",
    [
        (1, 1, 65535, False, False),  # Single port, full range
        (10, 1024, 49151, False, False),  # 10 registered ports
        (5, 49152, 65535, False, False),  # 5 ephemeral ports
        (1, 1, 10, False, False),  # Single port, small range
        (100, 1, 65535, False, False),  # Max count
        # Exclusion tests
        (5, 1, 65535, True, False),  # Exclude well-known
        (5, 1, 65535, False, True),  # Exclude common
        (5, 1024, 65535, True, True),  # Exclude both (wk already excluded by range)
        (5, 2000, 3000, True, True),  # Exclude both within a specific range
    ],
)
@pytest.mark.asyncio
async def test_generate_random_ports_success(
    client: TestClient, count: int, min_p: int, max_p: int, exclude_wk: bool, exclude_cmn: bool
):
    """Test successful generation of multiple random ports with various options."""
    params = f"count={count}&min_port={min_p}&max_port={max_p}&exclude_well_known={str(exclude_wk).lower()}&exclude_common={str(exclude_cmn).lower()}"
    response = client.get(f"/api/random-port/generate?{params}")

    assert response.status_code == status.HTTP_200_OK
    # Validate the JSON structure directly, as there's no multi-port response model
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert "ports" in response_data
    ports = response_data["ports"]
    assert isinstance(ports, list)
    assert len(ports) == count

    # Validate each port
    known_ports = _get_known_ports()
    common_ports = _get_common_ports()

    for port in ports:
        assert isinstance(port, int)
        assert min_p <= port <= max_p
        if exclude_wk:
            assert port > 1023 or port not in known_ports
        if exclude_cmn:
            assert port not in common_ports


@pytest.mark.parametrize(
    "params, error_substring",
    [
        ("count=0", "Input should be greater than or equal to 1"),
        ("count=101", "Input should be less than or equal to 100"),
        (f"min_port={MIN_PORT-1}", f"Input should be greater than or equal to {MIN_PORT}"),
        (f"max_port={MAX_PORT+1}", f"Input should be less than or equal to {MAX_PORT}"),
        ("min_port=100&max_port=50", "Minimum port cannot be greater than maximum port"),
        (
            "min_port=1&max_port=1000&exclude_well_known=true",
            "Cannot exclude well-known ports because the specified range is entirely within the well-known range",
        ),
        (
            "min_port=80&max_port=80&exclude_common=true",
            "The specified range and exclusions result in no available ports",
        ),
    ],
)
@pytest.mark.asyncio
async def test_generate_random_ports_invalid_input(client: TestClient, params: str, error_substring: str):
    """Test /generate endpoint with invalid parameters."""
    response = client.get(f"/api/random-port/generate?{params}")

    if (
        "Minimum port cannot be greater" in error_substring
        or "Cannot exclude well-known ports" in error_substring
        or "no available ports" in error_substring
    ):
        # These are 400 errors from endpoint logic
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error_substring in response.json()["detail"]
    else:
        # These are 422 validation errors from Query parameters
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # Update expected substrings based on actual Pydantic messages
        updated_error_substring = error_substring
        if "count=0" in params:
            updated_error_substring = "Input should be greater than or equal to 1"
        elif "count=101" in params:
            updated_error_substring = "Input should be less than or equal to 100"
        elif f"min_port={MIN_PORT-1}" in params:
            updated_error_substring = f"Input should be greater than or equal to {MIN_PORT}"
        elif f"max_port={MAX_PORT+1}" in params:
            updated_error_substring = f"Input should be less than or equal to {MAX_PORT}"

        assert updated_error_substring.lower() in str(response.json()).lower()


# --- Test Single Random Port Generation (/) ---
# Needs a separate response model


class SinglePortResponse(BaseModel):
    port: int
    range_type: str
    service_name: Optional[str] = None


@pytest.mark.parametrize(
    "port_type, protocol",
    [
        ("any", "tcp"),
        ("well-known", "tcp"),
        ("registered", "udp"),
        ("ephemeral", "tcp"),
    ],
)
@pytest.mark.asyncio
async def test_generate_single_random_port_success(client: TestClient, port_type: str, protocol: str):
    """Test successful generation of a single random port."""
    response = client.get(f"/api/random-port/?port_type={port_type}&protocol={protocol}")

    assert response.status_code == status.HTTP_200_OK
    # Validate against the manually defined model for this endpoint
    try:
        output = SinglePortResponse(**response.json())
    except Exception as e:
        pytest.fail(f"Response validation failed for single port: {e}\nResponse: {response.json()}")

    assert isinstance(output.port, int)
    assert MIN_PORT <= output.port <= MAX_PORT
    assert isinstance(output.range_type, str)
    assert len(output.range_type) > 0

    if port_type == "well-known":
        assert output.range_type == "Well-Known"
        assert 0 <= output.port <= 1023
    elif port_type == "registered":
        assert output.range_type == "Registered"
        assert 1024 <= output.port <= 49151
    elif port_type == "ephemeral":
        assert output.range_type == "Ephemeral (Dynamic/Private)"
        assert 49152 <= output.port <= 65535
    # 'any' range type is checked by the port value falling into one of the above

    # Service name can be None or string
    assert output.service_name is None or isinstance(output.service_name, str)


@pytest.mark.parametrize(
    "params, error_substring",
    [
        ("port_type=invalid", "String should match pattern '^(well-known|registered|ephemeral|any)$'"),
        ("protocol=ftp", "String should match pattern '^(tcp|udp)$'"),
    ],
)
@pytest.mark.asyncio
async def test_generate_single_random_port_invalid_params(client: TestClient, params: str, error_substring: str):
    """Test / endpoint with invalid query parameters."""
    response = client.get(f"/api/random-port/?{params}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Use case-insensitive comparison
    assert error_substring.lower() in str(response.json()).lower()
