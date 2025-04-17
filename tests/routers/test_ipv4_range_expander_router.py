import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from mcp_server.tools.ipv4_range_expander import MAX_ADDRESSES_TO_RETURN

# Import models defined within the router file
from models.ipv4_range_expander_models import IPv4RangeInput, IPv4RangeOutput
from routers.ipv4_range_expander_router import router as ipv4_range_expander_router

BASE_URL = "/expand-ipv4-range"


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
@pytest.mark.anyio
async def test_expand_ipv4_range_success(
    client: TestClient,
    ip_range_input: str,
    expected_count: int,
    expected_addresses: list[str],
    expected_truncated: bool,
):
    """Test successful expansion of valid IPv4 ranges (CIDR and hyphenated)."""
    payload = IPv4RangeInput(range_input=ip_range_input)
    response = client.post(BASE_URL, json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = IPv4RangeOutput(**response.json())

    assert output.count == expected_count
    assert output.truncated == expected_truncated

    if expected_truncated:
        assert len(output.addresses) == MAX_ADDRESSES_TO_RETURN
        # Check first address for truncated results
        assert output.addresses[0] == expected_addresses[0]
    elif expected_count == MAX_ADDRESSES_TO_RETURN:
        # Check first and last for full, non-truncated MAX_ADDRESSES case
        assert len(output.addresses) == MAX_ADDRESSES_TO_RETURN
        assert output.addresses[0] == expected_addresses[0]
        assert output.addresses[-1] == expected_addresses[-1]
    else:
        assert len(output.addresses) == expected_count
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
@pytest.mark.anyio
async def test_expand_ipv4_range_failure(client: TestClient, ip_range_input: str, error_substring: str):
    """Test expansion failures for invalid range formats or values."""
    payload = IPv4RangeInput(range_input=ip_range_input)
    response = client.post(BASE_URL, json=payload.model_dump())

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert error_substring.lower() in response.json()["detail"].lower()
