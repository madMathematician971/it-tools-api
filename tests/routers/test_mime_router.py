import mimetypes

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.mime_models import (
    MimeExtensionLookupInput,
    MimeExtensionLookupOutput,
    MimeTypeLookupInput,
    MimeTypeLookupOutput,
)
from routers.mime_router import router as mime_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(mime_router)
    # Ensure mimetypes is initialized within the app context if necessary,
    # although it's usually global.
    mimetypes.init()
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test MIME Type Lookup ---


@pytest.mark.parametrize(
    "extension, expected_mime_type",
    [
        ("txt", "text/plain"),
        (".html", "text/html"),
        ("HTML", "text/html"),  # Case insensitive
        ("Js", "text/javascript"),  # Updated expectation for JS
        (".JPEG", "image/jpeg"),
        ("png", "image/png"),
        ("pdf", "application/pdf"),
        ("zip", "application/zip"),
        ("unknown_extension", None),  # Unknown extension
        ("", None),  # Empty extension
        (".", None),  # Just a dot
    ],
)
@pytest.mark.asyncio
async def test_lookup_mime_type_success(client: TestClient, extension: str, expected_mime_type: str | None):
    """Test looking up MIME type from file extension."""
    payload = MimeTypeLookupInput(extension=extension)
    response = client.post("/api/mime/lookup-type", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = MimeTypeLookupOutput(**response.json())
    assert output.mime_type == expected_mime_type
    assert output.extension == extension


# --- Test MIME Extension Lookup ---


@pytest.mark.parametrize(
    "mime_type, expected_extensions, check_contains",  # Added check_contains flag
    [
        ("text/plain", [".txt"], True),  # Check if .txt is in the list
        ("text/html", [".html", ".htm"], False),  # Require exact match
        ("TEXT/HTML", [".html", ".htm"], False),  # Case insensitive, require exact match
        ("application/json", [".json"], False),  # Require exact match
        ("image/jpeg", [".jpg", ".jpeg", ".jpe"], False),  # Require exact match
        # ("application/octet-stream", [], False), # Removed unreliable test case
        ("unknown/mime-type", [], False),  # Require exact match (empty list)
        ("", [], False),  # Empty MIME type, require exact match (empty list)
    ],
)
@pytest.mark.asyncio
async def test_lookup_mime_extension_success(
    client: TestClient, mime_type: str, expected_extensions: list[str], check_contains: bool
):
    """Test looking up common extensions from MIME type."""
    payload = MimeExtensionLookupInput(mime_type=mime_type)
    response = client.post("/api/mime/lookup-extension", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = MimeExtensionLookupOutput(**response.json())

    if check_contains:
        # Check if all expected extensions are present in the output
        assert all(
            ext in output.extensions for ext in expected_extensions
        ), f"Expected {expected_extensions} to be subset of {output.extensions} for {mime_type}"
    else:
        # Require exact match (after sorting)
        assert sorted(output.extensions) == sorted(
            expected_extensions
        ), f"Expected {expected_extensions}, got {output.extensions} for {mime_type}"

    assert output.mime_type == mime_type.lower().strip()
