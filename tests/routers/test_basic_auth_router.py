import base64

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.basic_auth_models import BasicAuthInput, BasicAuthOutput
from routers.basic_auth_router import router as basic_auth_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(basic_auth_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Basic Auth Generation ---


@pytest.mark.parametrize(
    "username, password",
    [
        ("testuser", "testpass"),
        ("admin", "password123"),
        ("user@example.com", "complexP@$$w0rd"),
        ("", ""),  # Empty username and password
        ("user_with_spaces", "pass with spaces"),
        ("~!@#$%^&*()_+", "[]{};':\",./<>?"),  # Special characters
    ],
)
@pytest.mark.asyncio
async def test_basic_auth_generate_success(client: TestClient, username: str, password: str):
    """Test successful Basic Auth header generation."""
    payload = BasicAuthInput(username=username, password=password)
    response = client.post("/api/basic-auth/generate", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = BasicAuthOutput(**response.json())

    # Verify the components are returned correctly
    assert output.username == username
    assert output.password == password

    # Verify Base64 encoding
    expected_credentials = f"{username}:{password}"
    expected_base64 = base64.b64encode(expected_credentials.encode("utf-8")).decode("utf-8")
    assert output.base64 == expected_base64

    # Verify the full header string
    expected_header = f"Basic {expected_base64}"
    assert output.header == expected_header


# Test with invalid input types (should be caught by Pydantic)
@pytest.mark.asyncio
async def test_basic_auth_generate_invalid_input_type(client: TestClient):
    """Test providing invalid types for username/password."""
    response = client.post("/api/basic-auth/generate", json={"username": 123, "password": ["list"]})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
