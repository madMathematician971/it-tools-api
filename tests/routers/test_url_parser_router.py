import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.url_parser_models import UrlParserInput, UrlParserOutput
from routers.url_parser_router import router as url_parser_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(url_parser_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test URL Parsing ---


@pytest.mark.parametrize(
    "input_url, expected_components",
    [
        # Full URL with all components
        (
            "https://user:pass@example.com:8080/path/to/resource;param=value?query1=abc&query2=xyz#fragment",
            {
                "scheme": "https",
                "netloc": "user:pass@example.com:8080",
                "path": "/path/to/resource",
                "params": "param=value",
                "query": "query1=abc&query2=xyz",
                "fragment": "fragment",
                "username": "user",
                "password": "pass",
                "hostname": "example.com",
                "port": 8080,
                "query_params": {"query1": ["abc"], "query2": ["xyz"]},
                "error": None,
            },
        ),
        # Simple URL
        (
            "http://example.com",
            {
                "scheme": "http",
                "netloc": "example.com",
                "path": "",
                "params": "",
                "query": "",
                "fragment": "",
                "username": None,
                "password": None,
                "hostname": "example.com",
                "port": None,
                "query_params": {},
                "error": None,
            },
        ),
        # URL with path only
        (
            "/relative/path",
            {
                "scheme": "",
                "netloc": "",
                "path": "/relative/path",
                "params": "",
                "query": "",
                "fragment": "",
                "username": None,
                "password": None,
                "hostname": None,
                "port": None,
                "query_params": {},
                "error": None,
            },
        ),
        # URL with query parameters only
        (
            "?key=val&multi=1&multi=2",
            {
                "scheme": "",
                "netloc": "",
                "path": "",
                "params": "",
                "query": "key=val&multi=1&multi=2",
                "fragment": "",
                "username": None,
                "password": None,
                "hostname": None,
                "port": None,
                "query_params": {"key": ["val"], "multi": ["1", "2"]},
                "error": None,
            },
        ),
        # URL with fragment only
        (
            "#section-1",
            {
                "scheme": "",
                "netloc": "",
                "path": "",
                "params": "",
                "query": "",
                "fragment": "section-1",
                "username": None,
                "password": None,
                "hostname": None,
                "port": None,
                "query_params": {},
                "error": None,
            },
        ),
        # URL with username only
        (
            "ftp://user@ftp.example.com/",
            {
                "scheme": "ftp",
                "netloc": "user@ftp.example.com",
                "path": "/",
                "params": "",
                "query": "",
                "fragment": "",
                "username": "user",
                "password": None,
                "hostname": "ftp.example.com",
                "port": None,
                "query_params": {},
                "error": None,
            },
        ),
        # URL with IPv6 host
        (
            "http://[::1]:8080/",
            {
                "scheme": "http",
                "netloc": "[::1]:8080",
                "path": "/",
                "params": "",
                "query": "",
                "fragment": "",
                "username": None,
                "password": None,
                "hostname": "::1",  # Handled by urlparse
                "port": 8080,
                "query_params": {},
                "error": None,
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_parse_url_success(client: TestClient, input_url: str, expected_components: dict):
    """Test successful parsing of URLs into components."""
    payload = UrlParserInput(url=input_url)
    response = client.post("/api/url-parser/", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = UrlParserOutput(**response.json())

    assert output.original_url == input_url
    # Compare each expected component
    for key, value in expected_components.items():
        assert getattr(output, key) == value, f"Mismatch on component: {key}"


@pytest.mark.parametrize(
    "input_url, expected_status, error_substring",
    [
        ("", status.HTTP_400_BAD_REQUEST, "URL cannot be empty"),
        ("   ", status.HTTP_400_BAD_REQUEST, "URL cannot be empty"),
        # urllib.parse is very lenient, hard to find truly invalid URLs it fails on
        # Testing Pydantic validation if URL type were stricter could be added
    ],
)
@pytest.mark.asyncio
async def test_parse_url_errors(client: TestClient, input_url: str, expected_status: int, error_substring: str):
    """Test URL parsing with invalid or empty inputs."""
    payload = UrlParserInput(url=input_url)
    response = client.post("/api/url-parser/", json=payload.model_dump())

    assert response.status_code == expected_status
    assert error_substring in response.json()["detail"]
