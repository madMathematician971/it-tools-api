import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

# Import models defined within the router file
from routers.ipv4_range_expander_router import MAX_ADDRESSES_TO_RETURN, Ipv4RangeInput, Ipv4RangeOutput
from routers.ipv4_range_expander_router import router as ipv4_range_expander_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(ipv4_range_expander_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test IPv4 Range Expansion ---


@pytest.mark.parametrize(
    "ip_range_input, expected_count, expected_addresses, expected_truncated",
    [
        # CIDR tests
        ("192.168.1.0/30", 4, ["192.168.1.0", "192.168.1.1", "192.168.1.2", "192.168.1.3"], False),
        ("10.0.0.1/32", 1, ["10.0.0.1"], False),  # Single IP as CIDR
        ("172.16.5.10/32", 1, ["172.16.5.10"], False),
        ("0.0.0.0/31", 2, ["0.0.0.0", "0.0.0.1"], False),
        ("255.255.255.254/31", 2, ["255.255.255.254", "255.255.255.255"], False),
        # CIDR with host bits set (strict=False)
        ("192.168.1.1/24", 256, [f"192.168.1.{i}" for i in range(256)], False),
        # Hyphenated range tests
        ("192.168.1.10-192.168.1.12", 3, ["192.168.1.10", "192.168.1.11", "192.168.1.12"], False),
        (
            "10.1.1.254-10.1.2.1",
            4,
            ["10.1.1.254", "10.1.1.255", "10.1.2.0", "10.1.2.1"],
            False,
        ),  # Cross subnet boundary
        ("172.30.5.5-172.30.5.5", 1, ["172.30.5.5"], False),  # Single IP range
        # Single IP (should be treated as /32)
        ("1.1.1.1", 1, ["1.1.1.1"], False),
        ("8.8.8.8", 1, ["8.8.8.8"], False),
        # Truncation test (boundary case: exactly MAX_ADDRESSES)
        ("10.0.0.0/16", 65536, [f"10.0.{i//256}.{i%256}" for i in range(MAX_ADDRESSES_TO_RETURN)], False),
        # Truncation test for hyphenated range (boundary case)
        ("10.0.0.0-10.0.255.255", 65536, [f"10.0.{i//256}.{i%256}" for i in range(MAX_ADDRESSES_TO_RETURN)], False),
    ],
)
@pytest.mark.asyncio
async def test_expand_ipv4_range_success(
    client: TestClient,
    ip_range_input: str,
    expected_count: int,
    expected_addresses: list[str],
    expected_truncated: bool,
):
    """Test successful expansion of valid IPv4 ranges (CIDR and hyphenated)."""
    payload = Ipv4RangeInput(ip_range=ip_range_input)
    response = client.post("/api/ipv4-range-expander/expand", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = Ipv4RangeOutput(**response.json())

    assert output.count == expected_count
    assert output.truncated == expected_truncated
    assert output.addresses == expected_addresses


@pytest.mark.parametrize(
    "ip_range_input, error_substring",
    [
        # Invalid CIDR
        ("192.168.1.0/33", "Invalid IPv4 CIDR notation"),
        ("256.168.1.0/24", "Invalid IPv4 CIDR notation"),
        ("192.168.1.0 / 24", "Invalid IPv4 CIDR notation"),  # Space
        ("abc/24", "Invalid IPv4 CIDR notation"),
        # Invalid Hyphenated Range
        ("192.168.1.10-192.168.1.5", "Start IP address must be less than or equal"),  # Start > End
        ("192.168.1.10 - 192.168.1.5", "Start IP address must be less than or equal"),  # With spaces
        ("192.168.1.256-192.168.1.257", "Invalid IP address in range"),
        ("192.168.1.10-abc", "Invalid IP address in range"),
        ("192.168.1.10-192.168.1.11-192.168.1.12", "Invalid hyphenated range format"),  # Too many parts
        # Invalid Single IP / Format
        ("1.1.1.256", "Invalid input format"),
        ("a.b.c.d", "Invalid input format"),
        ("192.168..1", "Invalid input format"),
        # Empty input
        ("", "IP range input cannot be empty"),
    ],
)
@pytest.mark.asyncio
async def test_expand_ipv4_range_failure(client: TestClient, ip_range_input: str, error_substring: str):
    """Test expansion failures for invalid range formats or values."""
    payload = Ipv4RangeInput(ip_range=ip_range_input)
    response = client.post("/api/ipv4-range-expander/expand", json=payload.model_dump())

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert error_substring in response.json()["detail"]
