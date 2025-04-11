import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.ipv4_subnet_models import Ipv4SubnetInput, Ipv4SubnetOutput
from routers.ipv4_subnet_router import router as ipv4_subnet_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(ipv4_subnet_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test IPv4 Subnet Calculator ---


@pytest.mark.parametrize(
    "ip_cidr, expected",
    [
        # Standard /24 private network
        (
            "192.168.1.100/24",
            {
                "network_address": "192.168.1.0",
                "broadcast_address": "192.168.1.255",
                "netmask": "255.255.255.0",
                "cidr_prefix": 24,
                "num_addresses": 256,
                "num_usable_hosts": 254,
                "first_usable_host": "192.168.1.1",
                "last_usable_host": "192.168.1.254",
                "is_private": True,
                "is_multicast": False,
                "is_loopback": False,
                "error": None,
            },
        ),
        # Network address input /24
        (
            "192.168.1.0/24",
            {
                "network_address": "192.168.1.0",
                "broadcast_address": "192.168.1.255",
                "netmask": "255.255.255.0",
                "cidr_prefix": 24,
                "num_addresses": 256,
                "num_usable_hosts": 254,
                "first_usable_host": "192.168.1.1",
                "last_usable_host": "192.168.1.254",
                "is_private": True,
                "is_multicast": False,
                "is_loopback": False,
                "error": None,
            },
        ),
        # /30 network (4 addresses, 2 usable hosts)
        (
            "10.0.0.5/30",
            {
                "network_address": "10.0.0.4",
                "broadcast_address": "10.0.0.7",
                "netmask": "255.255.255.252",
                "cidr_prefix": 30,
                "num_addresses": 4,
                "num_usable_hosts": 2,
                "first_usable_host": "10.0.0.5",
                "last_usable_host": "10.0.0.6",
                "is_private": True,
                "is_multicast": False,
                "is_loopback": False,
                "error": None,
            },
        ),
        # /31 network (2 addresses, 0 usable hosts - often used for point-to-point)
        (
            "172.16.50.1/31",
            {
                "network_address": "172.16.50.0",
                "broadcast_address": "172.16.50.1",
                "netmask": "255.255.255.254",
                "cidr_prefix": 31,
                "num_addresses": 2,
                "num_usable_hosts": 0,
                "first_usable_host": None,
                "last_usable_host": None,
                "is_private": True,
                "is_multicast": False,
                "is_loopback": False,
                "error": None,
            },
        ),
        # /32 network (1 address, 0 usable hosts)
        (
            "8.8.8.8/32",
            {
                "network_address": "8.8.8.8",
                "broadcast_address": "8.8.8.8",
                "netmask": "255.255.255.255",
                "cidr_prefix": 32,
                "num_addresses": 1,
                "num_usable_hosts": 0,
                "first_usable_host": None,
                "last_usable_host": None,
                "is_private": False,
                "is_multicast": False,
                "is_loopback": False,
                "error": None,
            },
        ),
        # Loopback address
        (
            "127.0.0.1/8",
            {
                "network_address": "127.0.0.0",
                "broadcast_address": "127.255.255.255",
                "netmask": "255.0.0.0",
                "cidr_prefix": 8,
                "num_addresses": 16777216,
                "num_usable_hosts": 16777214,
                "first_usable_host": "127.0.0.1",
                "last_usable_host": "127.255.255.254",
                "is_private": True,
                "is_multicast": False,
                "is_loopback": True,
                "error": None,
            },
        ),
        # Using Netmask instead of CIDR
        (
            "192.168.1.100/255.255.255.0",
            {
                "network_address": "192.168.1.0",
                "broadcast_address": "192.168.1.255",
                "netmask": "255.255.255.0",
                "cidr_prefix": 24,
                "num_addresses": 256,
                "num_usable_hosts": 254,
                "first_usable_host": "192.168.1.1",
                "last_usable_host": "192.168.1.254",
                "is_private": True,
                "is_multicast": False,
                "is_loopback": False,
                "error": None,
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_ipv4_subnet_calculator_success(client: TestClient, ip_cidr: str, expected: dict):
    """Test successful subnet calculations for various valid inputs."""
    payload = Ipv4SubnetInput(ip_cidr=ip_cidr)
    response = client.post("/api/ipv4/subnet-calculator/", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = Ipv4SubnetOutput(**response.json())

    # Assert is_private directly first
    assert output.is_private == expected["is_private"], "is_private mismatch"

    # Compare the rest of the dictionary using model_dump, excluding is_private
    assert output.model_dump(exclude={"is_private"}) == {k: v for k, v in expected.items() if k != "is_private"}


@pytest.mark.parametrize(
    "ip_cidr, error_substring",
    [
        ("192.168.1.100/33", "does not appear to be an IPv4 or IPv6 network"),
        ("256.168.1.1/24", "does not appear to be an IPv4 or IPv6 network"),
        ("192.168.1.1/255.255.0.255", "does not appear to be an IPv4 or IPv6 network"),
        ("192.168.1.1/", "does not appear to be an IPv4 or IPv6 network"),
        ("abc/24", "does not appear to be an IPv4 or IPv6 network"),
        ("", "Input cannot be empty"),
    ],
)
@pytest.mark.asyncio
async def test_ipv4_subnet_calculator_failure(client: TestClient, ip_cidr: str, error_substring: str):
    """Test subnet calculations with various invalid inputs."""
    payload = Ipv4SubnetInput(ip_cidr=ip_cidr)
    response = client.post("/api/ipv4/subnet-calculator/", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = Ipv4SubnetOutput(**response.json())

    assert output.error is not None
    assert error_substring in output.error
    assert output.network_address is None
    assert output.cidr_prefix is None
