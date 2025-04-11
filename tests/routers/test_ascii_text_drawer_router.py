import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.ascii_text_drawer_models import AsciiTextDrawerRequest, AsciiTextDrawerResponse
from routers.ascii_text_drawer_router import router as ascii_text_drawer_router


# Fixture to create a FastAPI app instance with the router
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(ascii_text_drawer_router)
    return app


# Fixture to create a TestClient instance
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# Basic success test with default font and left alignment
@pytest.mark.asyncio
async def test_generate_ascii_art_default(client: TestClient):
    request_data = AsciiTextDrawerRequest(text="Hello", font="standard", alignment="left")
    response = client.post("/api/ascii-text-drawer/", json=request_data.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = AsciiTextDrawerResponse(**response.json())
    assert output.ascii_art is not None  # Check if art was generated
    assert output.font_used == "standard"  # Default font
    assert output.alignment == "left"  # Default alignment


# Test with a specific valid font
@pytest.mark.asyncio
async def test_generate_ascii_art_specific_font(client: TestClient):
    # Assuming 'slant' is a valid font installed with pyfiglet
    request_data = AsciiTextDrawerRequest(text="Test", font="slant", alignment="left")
    response = client.post("/api/ascii-text-drawer/", json=request_data.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = AsciiTextDrawerResponse(**response.json())
    assert output.ascii_art is not None
    assert output.font_used == "slant"
    assert output.alignment == "left"


# Test with an invalid font (should default to 'standard')
@pytest.mark.asyncio
async def test_generate_ascii_art_invalid_font(client: TestClient):
    request_data = AsciiTextDrawerRequest(text="Default", font="invalid-font-name", alignment="left")
    response = client.post("/api/ascii-text-drawer/", json=request_data.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = AsciiTextDrawerResponse(**response.json())
    assert output.ascii_art is not None
    assert output.font_used == "standard"  # Fallback font
    assert output.alignment == "left"


# Test center alignment
@pytest.mark.asyncio
async def test_generate_ascii_art_center_alignment(client: TestClient):
    request_data = AsciiTextDrawerRequest(text="Center", font="standard", alignment="center")
    response = client.post("/api/ascii-text-drawer/", json=request_data.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = AsciiTextDrawerResponse(**response.json())
    assert output.ascii_art is not None
    assert output.font_used == "standard"
    assert output.alignment == "center"


# Test right alignment
@pytest.mark.asyncio
async def test_generate_ascii_art_right_alignment(client: TestClient):
    request_data = AsciiTextDrawerRequest(text="Right", font="standard", alignment="right")
    response = client.post("/api/ascii-text-drawer/", json=request_data.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = AsciiTextDrawerResponse(**response.json())
    assert output.ascii_art is not None
    assert output.font_used == "standard"
    assert output.alignment == "right"


# Test with empty text input
@pytest.mark.asyncio
async def test_generate_ascii_art_empty_text(client: TestClient):
    request_data = AsciiTextDrawerRequest(text="", font="standard", alignment="left")
    response = client.post("/api/ascii-text-drawer/", json=request_data.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = AsciiTextDrawerResponse(**response.json())
    assert output.ascii_art == ""  # Expect empty string for empty input
    assert output.font_used == "standard"
    assert output.alignment == "left"


# Test with text containing special characters
@pytest.mark.asyncio
async def test_generate_ascii_art_special_chars(client: TestClient):
    request_data = AsciiTextDrawerRequest(text="!@#$%^&*()", font="standard", alignment="left")
    response = client.post("/api/ascii-text-drawer/", json=request_data.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = AsciiTextDrawerResponse(**response.json())
    # Just check if it runs without error and returns something
    assert output.ascii_art is not None
    assert output.font_used == "standard"
    assert output.alignment == "left"
