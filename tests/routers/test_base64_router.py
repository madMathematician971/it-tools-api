import base64
import io

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.base64_models import Base64DecodeFileRequest, InputString, OutputString
from routers.base64_router import router as base64_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(base64_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test String Encoding/Decoding ---


@pytest.mark.parametrize(
    "input_string, expected_encoded",
    [
        ("hello world", "aGVsbG8gd29ybGQ="),
        ("", ""),  # Empty string
        ("12345", "MTIzNDU="),
        ("!@#$%^&*()", "IUAjJCVeJiooKQ=="),
        ("你好世界", "5L2g5aW95LiW55WM"),  # Unicode characters
    ],
)
@pytest.mark.asyncio
async def test_base64_encode_success(client: TestClient, input_string: str, expected_encoded: str):
    payload = InputString(input=input_string)
    response = client.post("/api/base64/encode", json=payload.model_dump())
    assert response.status_code == status.HTTP_200_OK
    output = OutputString(**response.json())
    assert output.result == expected_encoded


@pytest.mark.parametrize(
    "encoded_string, expected_decoded",
    [
        ("aGVsbG8gd29ybGQ=", "hello world"),
        ("", ""),  # Empty string
        ("MTIzNDU=", "12345"),
        ("IUAjJCVeJiooKQ==", "!@#$%^&*()"),
        ("5L2g5aW95LiW55WM", "你好世界"),  # Unicode characters
        ("aGVsbG8gd29ybGQ", "hello world"),
    ],
)
@pytest.mark.asyncio
async def test_base64_decode_success(client: TestClient, encoded_string: str, expected_decoded: str):
    payload = InputString(input=encoded_string)
    response = client.post("/api/base64/decode", json=payload.model_dump())
    assert response.status_code == status.HTTP_200_OK
    output = OutputString(**response.json())
    assert output.result == expected_decoded


@pytest.mark.parametrize(
    "invalid_base64_string",
    [
        "invalid-base64!",  # Invalid characters
        "dGVzdA=== ",  # Incorrect padding or whitespace
    ],
)
@pytest.mark.asyncio
async def test_base64_decode_invalid_input(client: TestClient, invalid_base64_string: str):
    payload = InputString(input=invalid_base64_string)
    response = client.post("/api/base64/decode", json=payload.model_dump())
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid Base64 input string" in response.json()["detail"]


# --- Test File Encoding/Decoding ---


@pytest.mark.asyncio
async def test_base64_encode_file_success(client: TestClient):
    file_content = b"This is test file content."
    expected_encoded = base64.b64encode(file_content).decode("utf-8")
    file_obj = io.BytesIO(file_content)

    response = client.post(
        "/api/base64/encode-file",
        files={"file": ("test.txt", file_obj, "text/plain")},
    )

    assert response.status_code == status.HTTP_200_OK
    output = OutputString(**response.json())
    assert output.result == expected_encoded


@pytest.mark.asyncio
async def test_base64_encode_empty_file(client: TestClient):
    file_obj = io.BytesIO(b"")
    response = client.post(
        "/api/base64/encode-file",
        files={"file": ("empty.txt", file_obj, "text/plain")},
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_base64_decode_file_success(client: TestClient):
    original_content = b"Decode this file content."
    encoded_string = base64.b64encode(original_content).decode("utf-8")
    filename = "decoded_test.bin"

    payload = Base64DecodeFileRequest(base64_string=encoded_string, filename=filename)
    response = client.post("/api/base64/decode-file", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/octet-stream"
    assert f'attachment; filename="{filename}"' in response.headers["content-disposition"]
    assert response.content == original_content


@pytest.mark.asyncio
async def test_base64_decode_file_invalid_base64(client: TestClient):
    payload = Base64DecodeFileRequest(base64_string="invalid-base64!", filename="test.txt")
    response = client.post("/api/base64/decode-file", json=payload.model_dump())
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid Base64 input string" in response.json()["detail"]


@pytest.mark.asyncio
async def test_base64_decode_file_sanitize_filename(client: TestClient):
    original_content = b"test"
    encoded_string = base64.b64encode(original_content).decode("utf-8")
    unsafe_filename = "../unsafe/path/t?e*s:t|.txt"
    expected_safe_filename = "..unsafepathtest.txt"

    payload = Base64DecodeFileRequest(base64_string=encoded_string, filename=unsafe_filename)
    response = client.post("/api/base64/decode-file", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    assert f'attachment; filename="{expected_safe_filename}"' in response.headers["content-disposition"]
    assert response.content == original_content


@pytest.mark.asyncio
async def test_base64_decode_file_empty_filename(client: TestClient):
    original_content = b"test"
    encoded_string = base64.b64encode(original_content).decode("utf-8")
    empty_filename = ""
    expected_default_filename = "decoded_file"

    payload = Base64DecodeFileRequest(base64_string=encoded_string, filename=empty_filename)
    response = client.post("/api/base64/decode-file", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    assert f'attachment; filename="{expected_default_filename}"' in response.headers["content-disposition"]
    assert response.content == original_content
