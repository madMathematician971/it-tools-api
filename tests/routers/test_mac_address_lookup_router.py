from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from mac_vendor_lookup import VendorNotFoundError

from models.mac_address_lookup_models import MacLookupInput, MacLookupOutput
from routers.mac_address_lookup_router import router as mac_lookup_router


# Fixture to create a FastAPI app instance with the router
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(mac_lookup_router)
    return app


# Fixture to create a TestClient instance
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# Test cases
@pytest.mark.asyncio
@patch("routers.mac_address_lookup_router.mac_lookup_client", new_callable=AsyncMock)
async def test_mac_lookup_success(mock_mac_lookup, client: TestClient):
    """Test successful MAC address lookup."""
    if not mock_mac_lookup:  # Ensure the mock is created if the original client is None
        mock_mac_lookup = AsyncMock()
        mock_mac_lookup.async_lookup = AsyncMock()  # Mock the nested attribute if needed

    mock_mac_lookup.async_lookup.lookup = AsyncMock(return_value="Test Vendor Inc.")
    # Assign the mock back if it was created inside the test
    with patch("routers.mac_address_lookup_router.mac_lookup_client", mock_mac_lookup):
        input_data = MacLookupInput(mac_address="00:1A:2B:3C:4D:5E")
        response = client.post("/api/mac-address-lookup/", json=input_data.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = MacLookupOutput(**response.json())
    assert output.oui == "001A2B"
    assert output.company == "Test Vendor Inc."
    assert output.is_private is False
    assert output.error is None
    mock_mac_lookup.async_lookup.lookup.assert_awaited_once_with("00:1A:2B:3C:4D:5E")


@pytest.mark.asyncio
@patch("routers.mac_address_lookup_router.mac_lookup_client", new_callable=AsyncMock)
async def test_mac_lookup_vendor_not_found(mock_mac_lookup, client: TestClient):
    """Test MAC address lookup when vendor is not found."""

    if not mock_mac_lookup:
        mock_mac_lookup = AsyncMock()
        mock_mac_lookup.async_lookup = AsyncMock()

    test_mac = "11:22:33:44:55:66"
    mock_mac_lookup.async_lookup.lookup = AsyncMock(side_effect=VendorNotFoundError(test_mac))
    with patch("routers.mac_address_lookup_router.mac_lookup_client", mock_mac_lookup):
        input_data = MacLookupInput(mac_address=test_mac)
        response = client.post("/api/mac-address-lookup/", json=input_data.model_dump())

    assert response.status_code == status.HTTP_200_OK  # API handles this as success with error message
    output = MacLookupOutput(**response.json())
    assert output.oui == "112233"
    assert output.company is None
    assert output.is_private is False
    assert output.error == "Vendor not found for this OUI."
    mock_mac_lookup.async_lookup.lookup.assert_awaited_once_with(test_mac)


@pytest.mark.asyncio
async def test_mac_lookup_service_unavailable(client: TestClient):
    """Test MAC lookup when the mac_lookup_client is not initialized."""
    # Ensure the client is None for this test
    with patch("routers.mac_address_lookup_router.mac_lookup_client", None):
        input_data = MacLookupInput(mac_address="00:11:22:33:44:55")
        response = client.post("/api/mac-address-lookup/", json=input_data.model_dump())

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json()["detail"] == "MAC lookup service is not available."


@pytest.mark.asyncio
@patch("routers.mac_address_lookup_router.mac_lookup_client", new_callable=AsyncMock)
async def test_mac_lookup_locally_administered(mock_mac_lookup, client: TestClient):
    """Test MAC address lookup for a locally administered (private) address."""
    if not mock_mac_lookup:
        mock_mac_lookup = AsyncMock()
        mock_mac_lookup.async_lookup = AsyncMock()

    mock_mac_lookup.async_lookup.lookup = AsyncMock(return_value="Should Not Be Found Usually")
    with patch("routers.mac_address_lookup_router.mac_lookup_client", mock_mac_lookup):
        # MAC starting with x2, x6, xA, xE are locally administered
        input_data = MacLookupInput(mac_address="02:AA:BB:CC:DD:EE")
        response = client.post("/api/mac-address-lookup/", json=input_data.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = MacLookupOutput(**response.json())
    assert output.oui == "02AABB"
    # Vendor lookup might still succeed for the OUI part, but is_private should be True
    assert output.company == "Should Not Be Found Usually"
    assert output.is_private is True
    assert output.error is None
    mock_mac_lookup.async_lookup.lookup.assert_awaited_once_with("02:AA:BB:CC:DD:EE")


@pytest.mark.asyncio
async def test_mac_lookup_invalid_input_format(client: TestClient):
    """Test invalid input format (should be caught by Pydantic model)."""
    # Pydantic should raise validation error before the endpoint logic runs
    response = client.post("/api/mac-address-lookup/", json={"mac_address": "this is not a mac"})

    # FastAPI translates Pydantic validation errors to 422 Unprocessable Entity
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Don't assert specific error message content, as it depends on Pydantic internals
