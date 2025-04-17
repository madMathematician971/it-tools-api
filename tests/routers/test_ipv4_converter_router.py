import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.ipv4_converter_models import IPv4Input, IPv4Output
from routers.ipv4_converter_router import router as ipv4_converter_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(ipv4_converter_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test IPv4 Conversion ---


@pytest.mark.parametrize(
    "input_ip, input_format_hint, expected_dotted, expected_decimal, expected_hex, expected_binary",
    [
        # Auto-detection tests
        ("192.168.1.1", None, "192.168.1.1", 3232235777, "0xC0A80101", "11000000101010000000000100000001"),
        (3232235777, None, "192.168.1.1", 3232235777, "0xC0A80101", "11000000101010000000000100000001"),
        ("0xC0A80101", None, "192.168.1.1", 3232235777, "0xC0A80101", "11000000101010000000000100000001"),
        (
            "C0A80101",
            None,
            "192.168.1.1",
            3232235777,
            "0xC0A80101",
            "11000000101010000000000100000001",
        ),  # Hex without 0x
        (
            "11000000101010000000000100000001",
            None,
            "192.168.1.1",
            3232235777,
            "0xC0A80101",
            "11000000101010000000000100000001",
        ),
        ("10.0.0.1", None, "10.0.0.1", 167772161, "0x0A000001", "00001010000000000000000000000001"),
        (167772161, None, "10.0.0.1", 167772161, "0x0A000001", "00001010000000000000000000000001"),
        ("0x0A000001", None, "10.0.0.1", 167772161, "0x0A000001", "00001010000000000000000000000001"),
        (
            "00001010000000000000000000000001",
            None,
            "10.0.0.1",
            167772161,
            "0x0A000001",
            "00001010000000000000000000000001",
        ),
        ("0.0.0.0", None, "0.0.0.0", 0, "0x00000000", "00000000000000000000000000000000"),
        ("255.255.255.255", None, "255.255.255.255", 4294967295, "0xFFFFFFFF", "11111111111111111111111111111111"),
        (4294967295, None, "255.255.255.255", 4294967295, "0xFFFFFFFF", "11111111111111111111111111111111"),
        ("0xFFFFFFFF", None, "255.255.255.255", 4294967295, "0xFFFFFFFF", "11111111111111111111111111111111"),
        (
            "11111111111111111111111111111111",
            None,
            "255.255.255.255",
            4294967295,
            "0xFFFFFFFF",
            "11111111111111111111111111111111",
        ),
        # Format hint tests
        ("192.168.1.1", "dotted", "192.168.1.1", 3232235777, "0xC0A80101", "11000000101010000000000100000001"),
        (3232235777, "decimal", "192.168.1.1", 3232235777, "0xC0A80101", "11000000101010000000000100000001"),
        ("0xC0A80101", "hex", "192.168.1.1", 3232235777, "0xC0A80101", "11000000101010000000000100000001"),
        (
            "C0A80101",
            "hex",
            "192.168.1.1",
            3232235777,
            "0xC0A80101",
            "11000000101010000000000100000001",
        ),  # Hex hint without 0x
        (
            "11000000101010000000000100000001",
            "binary",
            "192.168.1.1",
            3232235777,
            "0xC0A80101",
            "11000000101010000000000100000001",
        ),
        ("1010", "binary", "0.0.0.10", 10, "0x0000000A", "00000000000000000000000000001010"),  # Short binary with hint
    ],
)
@pytest.mark.asyncio
async def test_ipv4_convert_success(
    client: TestClient,
    input_ip,
    input_format_hint: str | None,
    expected_dotted: str,
    expected_decimal: int,
    expected_hex: str,
    expected_binary: str,
):
    """Test successful IPv4 conversions with and without format hints."""
    payload = IPv4Input(ip_address=str(input_ip), format=input_format_hint)
    response = client.post("/api/ipv4-converter/", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = IPv4Output(**response.json())

    assert output.error is None
    assert output.dotted_decimal == expected_dotted
    assert output.decimal == expected_decimal
    assert output.hexadecimal == expected_hex
    assert output.binary == expected_binary
    assert output.original == str(input_ip)


@pytest.mark.parametrize(
    "input_ip, input_format_hint, error_substring",
    [
        # Auto-detect failures
        ("256.168.1.1", None, "Could not determine IP address format"),
        ("192.168.1", None, "Could not determine IP address format"),
        ("192.168.1.1.1", None, "Could not determine IP address format"),
        ("C0A801XYZ", None, "Could not determine IP address format"),
        ("0xG0A80101", None, "Could not determine IP address format"),
        ("110000001010100000000001000000010", None, "Binary IP must be at most 32 bits"),
        (4294967296, None, "Invalid or out-of-range decimal IP format"),
        (-1, None, "Could not determine IP address format"),
        ("", None, "IP address cannot be empty"),
        # Format hint failures
        ("192.168.1.256", "dotted", "Octet 256 (> 255) not permitted"),
        ("not a number", "decimal", "Invalid decimal IP format"),
        (4294967296, "decimal", "Invalid decimal IP format"),
        ("0xGHIJKLM", "hex", "Invalid hexadecimal IP format"),
        ("101010102", "binary", "Invalid binary IP format"),
        # ("192.168.1.1", "unknown", "Unknown format hint"), # Commented out: Pydantic validation catches this.
        ("192.168.1.1", "hex", "Invalid hexadecimal IP format"),
        (3232235777, "binary", "Invalid binary IP format"),
    ],
)
@pytest.mark.asyncio
async def test_ipv4_convert_failure(client: TestClient, input_ip, input_format_hint: str | None, error_substring: str):
    """Test IPv4 conversions that should fail due to invalid input or format."""
    payload = IPv4Input(ip_address=str(input_ip), format=input_format_hint)
    response = client.post("/api/ipv4-converter/", json=payload.model_dump())

    # Expect 400 Bad Request for validation errors now
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Check the error message in the detail field
    response_data = response.json()
    assert "detail" in response_data
    assert error_substring.lower() in response_data["detail"].lower()
