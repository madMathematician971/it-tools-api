import ipaddress  # To validate the output address format
import re

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.ipv6_ula_models import Ipv6UlaResponse  # Assuming models are separate
from routers.ipv6_ula_router import router as ipv6_ula_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(ipv6_ula_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test IPv6 ULA Generation ---


# Helper to validate ULA format
def validate_ula(ula_str: str, global_id: str, subnet_id: str):
    try:
        addr = ipaddress.IPv6Address(ula_str)
        assert addr.is_private  # ULAs are private
        # Check prefix fd00::/8
        assert (int(addr) >> 120) == 0xFD
        # Reconstruct the expected prefix from components and check
        expected_prefix_str = f"fd{global_id[:2]}:{global_id[2:6]}:{global_id[6:]}:{subnet_id}::"
        # Allow for different interface IDs (like ::1)
        assert ula_str.startswith(expected_prefix_str[:-1])  # Check up to the last ::
        # Check global and subnet parts specifically (case-insensitive)
        parts = addr.exploded.split(":")
        assert parts[0] == "fd" + global_id[:2]
        assert parts[1] == global_id[2:6]
        assert parts[2] == global_id[6:]
        assert parts[3] == subnet_id
        return True
    except Exception:
        return False


@pytest.mark.asyncio
async def test_generate_ula_random_global_id(client: TestClient):
    """Test generating ULA with a random Global ID and default Subnet ID."""
    response = client.get("/api/ipv6-ula/")

    assert response.status_code == status.HTTP_200_OK
    output = Ipv6UlaResponse(**response.json())

    assert re.match(r"^[0-9a-f]{10}$", output.global_id)
    assert output.subnet_id == "0001"
    assert validate_ula(output.ula_address, output.global_id, output.subnet_id)


@pytest.mark.asyncio
async def test_generate_ula_with_global_id(client: TestClient):
    """Test generating ULA with a specified Global ID."""
    test_global_id = "a1b2c3d4e5"
    response = client.get(f"/api/ipv6-ula/?global_id={test_global_id}")

    assert response.status_code == status.HTTP_200_OK
    output = Ipv6UlaResponse(**response.json())

    assert output.global_id == test_global_id
    assert output.subnet_id == "0001"
    assert validate_ula(output.ula_address, output.global_id, output.subnet_id)


@pytest.mark.asyncio
async def test_generate_ula_with_subnet_id(client: TestClient):
    """Test generating ULA with a specified Subnet ID."""
    test_subnet_id = "abcd"
    response = client.get(f"/api/ipv6-ula/?subnet_id={test_subnet_id}")

    assert response.status_code == status.HTTP_200_OK
    output = Ipv6UlaResponse(**response.json())

    assert re.match(r"^[0-9a-f]{10}$", output.global_id)
    assert output.subnet_id == test_subnet_id
    assert validate_ula(output.ula_address, output.global_id, output.subnet_id)


@pytest.mark.asyncio
async def test_generate_ula_with_both_ids(client: TestClient):
    """Test generating ULA with specified Global and Subnet IDs."""
    test_global_id = "1122334455"
    test_subnet_id = "beef"
    response = client.get(f"/api/ipv6-ula/?global_id={test_global_id}&subnet_id={test_subnet_id}")

    assert response.status_code == status.HTTP_200_OK
    output = Ipv6UlaResponse(**response.json())

    assert output.global_id == test_global_id
    assert output.subnet_id == test_subnet_id
    assert validate_ula(output.ula_address, output.global_id, output.subnet_id)
    assert output.ula_address == "fd11:2233:4455:beef::1"


@pytest.mark.parametrize(
    "query_params, error_substring",
    [
        ("global_id=12345", "String should have at least 10 characters"),
        ("global_id=123456789", "String should have at least 10 characters"),
        ("global_id=1234567890a", "String should have at most 10 characters"),
        ("global_id=xyz1234567", "String should match pattern"),
        ("subnet_id=123", "String should have at least 4 characters"),
        ("subnet_id=12345", "String should have at most 4 characters"),
        ("subnet_id=ghij", "String should match pattern"),
    ],
)
@pytest.mark.asyncio
async def test_generate_ula_invalid_params(client: TestClient, query_params: str, error_substring: str):
    """Test ULA generation with invalid query parameter formats (should be caught by FastAPI/Pydantic)."""
    response = client.get(f"/api/ipv6-ula/?{query_params}")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Check if the specific error detail is present in the response
    response_data = response.json()
    assert "detail" in response_data
    assert isinstance(response_data["detail"], list), "Expected Pydantic v2 error format"
    error_found = False
    for error in response_data["detail"]:
        if error_substring in error.get("msg", ""):
            error_found = True
            break
    assert error_found, f"Expected error substring '{error_substring}' not found in details: {response_data['detail']}"
