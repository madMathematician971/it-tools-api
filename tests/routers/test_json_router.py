import json

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.json_models import JsonFormatInput, JsonOutput, JsonTextInput
from routers.json_router import router as json_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(json_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test JSON Formatting ---

# Sample Data
SAMPLE_DICT = {"c": 3, "a": 1, "b": {"nested": True, "list": [2, 1]}}
SAMPLE_UNFORMATTED_JSON = json.dumps(SAMPLE_DICT, separators=(",", ":"))  # Minified
SAMPLE_FORMATTED_JSON_INDENT2_NOSORT = json.dumps(SAMPLE_DICT, indent=2, sort_keys=False)
SAMPLE_FORMATTED_JSON_INDENT4_SORTED = json.dumps(SAMPLE_DICT, indent=4, sort_keys=True)


@pytest.mark.parametrize(
    "input_json, indent, sort_keys, expected_formatted_json",
    [
        (SAMPLE_UNFORMATTED_JSON, 2, False, SAMPLE_FORMATTED_JSON_INDENT2_NOSORT),
        (SAMPLE_FORMATTED_JSON_INDENT2_NOSORT, 4, True, SAMPLE_FORMATTED_JSON_INDENT4_SORTED),
        ('{"key": "value"}', 4, False, '{\n    "key": "value"\n}'),
        ("[1, 3, 2]", 2, True, "[\n  1,\n  3,\n  2\n]"),  # Sorting doesn't affect list elements, only dict keys
        ("[1, 3, 2]", 2, False, "[\n  1,\n  3,\n  2\n]"),
        # Unicode
        ('{"name": "你好"}', 2, False, '{\n  "name": "你好"\n}'),
    ],
)
@pytest.mark.asyncio
async def test_format_json_success(
    client: TestClient, input_json: str, indent: int, sort_keys: bool, expected_formatted_json: str
):
    """Test successful JSON formatting with different options."""
    payload = JsonFormatInput(json_string=input_json, indent=indent, sort_keys=sort_keys)
    response = client.post("/api/json/format", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = JsonOutput(**response.json())
    # Direct string comparison should work as json.dumps is deterministic with these options
    assert output.result_string == expected_formatted_json


@pytest.mark.asyncio
async def test_format_json_invalid_input(client: TestClient):
    """Test JSON formatting with invalid JSON input."""
    # Ensure all required arguments are provided
    payload = JsonFormatInput(json_string='{"key": invalid}', indent=2, sort_keys=False)
    response = client.post("/api/json/format", json=payload.model_dump())

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid JSON input" in response.json()["detail"]


# --- Test JSON Minification ---


@pytest.mark.parametrize(
    "input_json, expected_minified_json",
    [
        (SAMPLE_FORMATTED_JSON_INDENT4_SORTED, SAMPLE_UNFORMATTED_JSON),
        (SAMPLE_FORMATTED_JSON_INDENT2_NOSORT, SAMPLE_UNFORMATTED_JSON),
        ('{\n  "key": "value"\n}', '{"key":"value"}'),
        ("[\n  1,\n  2,\n  3\n]", "[1,2,3]"),
        (' { "a" : 1 } ', '{"a":1}'),  # Extra whitespace
        ('{"name": "你好"}', '{"name":"你好"}'),  # Unicode
    ],
)
@pytest.mark.asyncio
async def test_minify_json_success(client: TestClient, input_json: str, expected_minified_json: str):
    """Test successful JSON minification."""
    payload = JsonTextInput(json_string=input_json)
    response = client.post("/api/json/minify", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = JsonOutput(**response.json())
    # Parse and compare objects to handle potential key order differences if input wasn't sorted
    assert json.loads(output.result_string) == json.loads(expected_minified_json)
    # Also check string length for basic minification check
    assert len(output.result_string) <= len(input_json)  # Minified should be shorter or equal


@pytest.mark.asyncio
async def test_minify_json_invalid_input(client: TestClient):
    """Test JSON minification with invalid JSON input."""
    payload = JsonTextInput(json_string="[1, 2, invalid]")
    response = client.post("/api/json/minify", json=payload.model_dump())

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid JSON input" in response.json()["detail"]
