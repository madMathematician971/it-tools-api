import uuid

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.uuid_models import UuidResponse
from routers.uuid_router import router as uuid_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(uuid_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test UUID Generation ---


@pytest.mark.parametrize("version", [1, 4])
@pytest.mark.asyncio
async def test_generate_uuid_success(client: TestClient, version: int):
    """Test successful generation of UUID versions 1 and 4."""
    response = client.get(f"/api/uuid/?version={version}")

    assert response.status_code == status.HTTP_200_OK
    output = UuidResponse(**response.json())

    # Validate basic format and version
    assert isinstance(output.uuid, str)
    try:
        parsed_uuid = uuid.UUID(output.uuid)
        assert parsed_uuid.version == version
    except ValueError:
        pytest.fail(f"Generated UUID ({output.uuid}) is not a valid format")

    # Validate other fields
    assert output.version == version
    assert output.variant == "RFC 4122"
    assert output.is_nil is False
    assert output.hex == parsed_uuid.hex
    assert output.bytes == parsed_uuid.bytes.hex()
    assert output.urn == parsed_uuid.urn
    assert output.integer == parsed_uuid.int

    # Validate binary string
    assert isinstance(output.binary, str)
    assert len(output.binary) == 128
    assert all(c in "01" for c in output.binary)
    # Optional: Convert binary back to int and compare
    assert int(output.binary, 2) == parsed_uuid.int


@pytest.mark.parametrize(
    "invalid_version, expected_status, error_substring",
    [
        (
            0,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "input should be greater than or equal to 1",
        ),  # Pydantic validation
        (
            5,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "input should be less than or equal to 4",
        ),  # Pydantic validation
        (2, status.HTTP_400_BAD_REQUEST, "Unsupported UUID version: 2"),  # Endpoint logic
        (3, status.HTTP_400_BAD_REQUEST, "Unsupported UUID version: 3"),  # Endpoint logic
        (
            "abc",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "input should be a valid integer",
        ),  # Pydantic validation
    ],
)
@pytest.mark.asyncio
async def test_generate_uuid_invalid_version(
    client: TestClient, invalid_version: int | str, expected_status: int, error_substring: str
):
    """Test UUID generation with invalid or unsupported versions."""
    response = client.get(f"/api/uuid/?version={invalid_version}")

    assert response.status_code == expected_status
    if expected_status == status.HTTP_422_UNPROCESSABLE_ENTITY:
        assert error_substring.lower() in str(response.json()).lower()
    elif expected_status == status.HTTP_400_BAD_REQUEST:
        assert error_substring is not None
        # Add explicit check for detail in 400 errors
        assert error_substring.lower() in response.json()["detail"].lower()
