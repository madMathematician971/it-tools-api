import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.user_agent_parser_models import UserAgentInput, UserAgentOutput
from routers.user_agent_parser_router import router as ua_parser_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(ua_parser_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test User Agent Parsing ---

# Sample User Agent Strings
UA_CHROME_WINDOWS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
)
UA_FIREFOX_MACOS = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0"
UA_SAFARI_IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
UA_EDGE_ANDROID = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36 EdgA/114.0.1823.79"
UA_GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
UA_EMPTY = ""
UA_INVALID = "Not a user agent string"


@pytest.mark.parametrize(
    "input_ua, expected_browser_family, expected_os_family, expected_device_family, is_mobile, is_pc, is_bot",
    [
        (UA_CHROME_WINDOWS, "Chrome", "Windows", "Other", False, True, False),
        (UA_FIREFOX_MACOS, "Firefox", "Mac OS X", "Mac", False, True, False),
        (UA_SAFARI_IPHONE, "Mobile Safari", "iOS", "iPhone", True, False, False),
        (UA_EDGE_ANDROID, "Edge Mobile", "Android", "K", True, False, False),
        (UA_GOOGLEBOT, "Googlebot", "Other", "Spider", False, False, True),
        # Invalid UA might parse as 'Other' or similar depending on the library
        (UA_INVALID, "Other", "Other", "Other", False, False, False),
    ],
)
@pytest.mark.asyncio
async def test_parse_user_agent_success(
    client: TestClient,
    input_ua: str,
    expected_browser_family: str,
    expected_os_family: str,
    expected_device_family: str,
    is_mobile: bool,
    is_pc: bool,
    is_bot: bool,
):
    """Test successful parsing of various User-Agent strings."""
    payload = UserAgentInput(user_agent=input_ua)
    response = client.post("/api/user-agent-parser/", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = UserAgentOutput(**response.json())

    assert output.raw_user_agent == input_ua

    # Basic checks on extracted families and flags
    assert output.browser is not None
    assert output.os is not None
    assert output.device is not None

    # Assign to new variables after None checks to help type checker
    browser_data = output.browser
    os_data = output.os
    device_data = output.device

    assert browser_data["family"] == expected_browser_family
    assert os_data["family"] == expected_os_family
    assert device_data["family"] == expected_device_family
    assert device_data["is_mobile"] == is_mobile
    assert device_data["is_pc"] == is_pc
    assert device_data["is_bot"] == is_bot

    # Check if version strings are populated (can be complex to assert exact versions)
    assert isinstance(browser_data["version"], str)
    assert isinstance(os_data["version"], str)
    # Check that major versions are strings (or empty strings)
    assert isinstance(browser_data["version_major"], str)
    assert isinstance(os_data["version_major"], str)
    # Check device brand/model are strings
    assert isinstance(device_data["brand"], str)
    assert isinstance(device_data["model"], str)


@pytest.mark.parametrize(
    "input_ua, expected_status, error_substring",
    [
        (UA_EMPTY, status.HTTP_400_BAD_REQUEST, "User-Agent string cannot be empty"),
        ("   ", status.HTTP_400_BAD_REQUEST, "User-Agent string cannot be empty"),
    ],
)
@pytest.mark.asyncio
async def test_parse_user_agent_empty(client: TestClient, input_ua: str, expected_status: int, error_substring: str):
    """Test parsing with empty or whitespace-only User-Agent string."""
    payload = UserAgentInput(user_agent=input_ua)
    response = client.post("/api/user-agent-parser/", json=payload.model_dump())

    assert response.status_code == expected_status
    assert error_substring in response.json()["detail"]


# Test invalid input type (Pydantic validation)
@pytest.mark.asyncio
async def test_parse_user_agent_invalid_type(client: TestClient):
    """Test providing invalid type for user_agent input."""
    response = client.post("/api/user-agent-parser/", json={"user_agent": 1234})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "input should be a valid string" in str(response.json()).lower()
