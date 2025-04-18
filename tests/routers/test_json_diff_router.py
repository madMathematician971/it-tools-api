import json

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.json_diff_models import JsonDiffInput, JsonDiffOutput
from routers.json_diff_router import router as json_diff_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(json_diff_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test JSON Diff ---

# Sample JSON data
JSON1_BASE = {"name": "Alice", "age": 30, "city": "New York", "pets": ["cat", "dog"]}
JSON2_SAME = {"name": "Alice", "age": 30, "city": "New York", "pets": ["cat", "dog"]}
JSON3_AGE_CHANGED = {"name": "Alice", "age": 31, "city": "New York", "pets": ["cat", "dog"]}
JSON4_CITY_REMOVED = {"name": "Alice", "age": 30, "pets": ["cat", "dog"]}
JSON5_PET_ADDED = {"name": "Alice", "age": 30, "city": "New York", "pets": ["cat", "dog", "fish"]}
JSON6_PET_ORDER_CHANGED = {"name": "Alice", "age": 30, "city": "New York", "pets": ["dog", "cat"]}
JSON7_WHITESPACE = {" name ": " Alice ", "age": 30}
JSON8_NO_WHITESPACE = {"age": 30, "name": "Alice"}


@pytest.mark.parametrize(
    "json1, json2, ignore_order, output_format, expect_diff, expect_error",
    [
        # Basic diffs
        (JSON1_BASE, JSON3_AGE_CHANGED, False, "simple", True, None),  # Age changed
        (JSON1_BASE, JSON4_CITY_REMOVED, False, "simple", True, None),  # City removed
        (JSON1_BASE, JSON5_PET_ADDED, False, "simple", True, None),  # Pet added
        (JSON1_BASE, JSON6_PET_ORDER_CHANGED, False, "simple", True, None),  # Order changed (diff detected)
        (JSON1_BASE, JSON2_SAME, False, "simple", False, None),  # Identical
        # ignore_order
        (JSON1_BASE, JSON6_PET_ORDER_CHANGED, True, "simple", False, None),  # Order ignored (no diff)
        (JSON1_BASE, JSON5_PET_ADDED, True, "simple", True, None),  # Item added still detected
        # ignore_whitespace (Note: DeepDiff ignore_whitespace affects keys/values with surrounding whitespace)
        # This functionality is removed as DeepDiff doesn't support it directly.
        (JSON7_WHITESPACE, JSON8_NO_WHITESPACE, False, "simple", True, None),  # Whitespace significant (default)
        # Output formats
        (JSON1_BASE, JSON3_AGE_CHANGED, False, "delta", True, None),  # Delta format
        (JSON1_BASE, JSON2_SAME, False, "delta", False, None),  # Delta format - no diff
        # Invalid JSON
        (JSON1_BASE, "invalid json", False, "simple", False, "Invalid JSON in second input"),
        ('{"key": invalid}', JSON1_BASE, False, "simple", False, "Invalid JSON in first input"),
        # Invalid output format
        (JSON1_BASE, JSON2_SAME, False, "invalid_format", False, "Invalid output format"),
    ],
)
@pytest.mark.asyncio
async def test_json_diff(
    client: TestClient,
    json1,
    json2,
    ignore_order: bool,
    output_format: str,
    expect_diff: bool,
    expect_error: str | None,
):
    """Test JSON diff generation with various options and inputs."""
    # Convert dicts to JSON strings for the payload
    json1_str = json.dumps(json1) if isinstance(json1, dict) else str(json1)
    json2_str = json.dumps(json2) if isinstance(json2, dict) else str(json2)

    payload = JsonDiffInput(
        json1=json1_str,
        json2=json2_str,
        ignore_order=ignore_order,
        output_format=output_format,
    )
    response = client.post("/api/json-diff/", json=payload.model_dump())

    if expect_error:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert "detail" in response_data
        # Check if the expected error message is a substring of the detail
        assert expect_error in response_data["detail"]
    else:
        # Expecting successful diff generation
        assert response.status_code == status.HTTP_200_OK
        output = JsonDiffOutput(**response.json())
        assert output.error is None

        # Check if diff exists or not
        if expect_diff:
            assert output.diff != "", "Expected a diff, but none was generated."
            # Check format used matches expectation
            if output_format == "delta":
                assert output.format_used == "delta"
                try:
                    json.loads(output.diff)  # Check if delta output is valid JSON
                except json.JSONDecodeError:
                    pytest.fail("Delta output format was not valid JSON")
            else:
                assert output.format_used == "simple"
                # Simple output is just a string, no further structural check needed
        else:
            # Allow empty string OR empty dict for delta format
            allowed_empty = [""]
            if output.format_used == "delta":
                allowed_empty.append("{}")
            assert output.diff in allowed_empty, f"Expected no diff, but got: {output.diff}"
            assert output.format_used == output_format
