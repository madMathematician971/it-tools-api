import csv
import io
import json

import pytest
from deepdiff import DeepDiff
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.json_csv_converter_models import JsonCsvInput, JsonCsvOutput
from routers.json_csv_converter_router import router as json_csv_converter_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(json_csv_converter_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test JSON <-> CSV Conversion ---

# Sample Data
SAMPLE_JSON_LIST = [
    {"id": 1, "name": "Alice", "city": "New York"},
    {"id": 2, "name": "Bob", "city": "London"},
    {"id": 3, "name": "Charlie", "city": "Paris", "extra": "data"},  # Extra field
]
SAMPLE_JSON_STRING = json.dumps(
    [
        {"id": "1", "name": "Alice", "city": "New York", "extra": ""},
        {"id": "2", "name": "Bob", "city": "London", "extra": ""},
        {"id": "3", "name": "Charlie", "city": "Paris", "extra": "data"},
    ],
    indent=2,
)

SAMPLE_CSV_STRING_COMMA = "id,name,city,extra\r\n1,Alice,New York,\r\n2,Bob,London,\r\n3,Charlie,Paris,data\r\n"
SAMPLE_CSV_STRING_SEMICOLON = "id;name;city;extra\r\n1;Alice;New York;\r\n2;Bob;London;\r\n3;Charlie;Paris;data\r\n"


# Helper to compare CSV content ignoring line endings and header order
def compare_csv(csv1: str, csv2: str, delimiter: str) -> bool:
    """Compare two CSV strings, ignoring row/column order and whitespace."""
    try:
        reader1 = csv.DictReader(io.StringIO(csv1), delimiter=delimiter)
        reader2 = csv.DictReader(io.StringIO(csv2), delimiter=delimiter)
        # Normalize by sorting based on a string representation of each row dict
        data1 = sorted(list(reader1), key=lambda x: json.dumps(x, sort_keys=True))
        data2 = sorted(list(reader2), key=lambda x: json.dumps(x, sort_keys=True))
        return data1 == data2
    except Exception:
        return False  # If parsing fails, they are not equal


# Helper to compare JSON (list of dicts)
# Converts to set of tuples for order-insensitive comparison
def compare_json_list_of_dicts(json_str1: str, json_str2: str) -> bool:
    """Compare two JSON strings representing lists of dictionaries, ignoring order and types."""
    try:
        list1 = json.loads(json_str1)
        list2 = json.loads(json_str2)
        # DeepDiff for robust comparison, ignoring list order and specific type changes
        diff = DeepDiff(
            list1,
            list2,
            ignore_order=True,
            ignore_numeric_type_changes=True,
            ignore_string_type_changes=True,
            report_repetition=True,
            verbose_level=0,
        )
        return not diff  # No differences means they match
    except Exception:
        return False


# --- Conversion Tests ---


@pytest.mark.parametrize(
    "input_data, delimiter, expected_format, expected_data_string",
    [
        (SAMPLE_JSON_STRING, ",", "CSV", SAMPLE_CSV_STRING_COMMA),
        (SAMPLE_JSON_STRING, ";", "CSV", SAMPLE_CSV_STRING_SEMICOLON),
        (SAMPLE_CSV_STRING_COMMA, ",", "JSON", SAMPLE_JSON_STRING),
        (SAMPLE_CSV_STRING_SEMICOLON, ";", "JSON", SAMPLE_JSON_STRING),
        # Test with single JSON object
        (json.dumps({"a": 1, "b": 2}), ",", "CSV", "a,b\r\n1,2\r\n"),
        # Test with CSV having different column order (should still match JSON)
        (
            "name,id,city\r\nAlice,1,New York\r\nBob,2,London",
            ",",
            "JSON",
            json.dumps(
                [{"id": "1", "name": "Alice", "city": "New York"}, {"id": "2", "name": "Bob", "city": "London"}],
                indent=2,
            ),
        ),
    ],
)
@pytest.mark.asyncio
async def test_json_csv_conversion_success(
    client: TestClient, input_data: str, delimiter: str, expected_format: str, expected_data_string: str
):
    """Test successful conversion between JSON and CSV formats."""
    payload = JsonCsvInput(data=input_data, delimiter=delimiter)
    response = client.post("/api/json-csv-converter/", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = JsonCsvOutput(**response.json())
    assert output.format == expected_format

    if expected_format == "CSV":
        assert compare_csv(output.result, expected_data_string, delimiter)
    elif expected_format == "JSON":
        assert compare_json_list_of_dicts(output.result, expected_data_string)
    else:
        pytest.fail(f"Unexpected format: {expected_format}")


@pytest.mark.parametrize(
    "input_data, delimiter, error_substring",
    [
        # Test case for invalid JSON (list of non-objects)
        ("[1, 2, 3]", ",", "Each item in the JSON array must be an object"),
        # Test case for empty input data
        ("", ",", "Input data cannot be empty"),
    ],
)
@pytest.mark.asyncio
async def test_json_csv_conversion_failure(client: TestClient, input_data: str, delimiter: str, error_substring: str):
    """Test conversion failures due to invalid input formats."""
    payload = JsonCsvInput(data=input_data, delimiter=delimiter)
    response = client.post("/api/json-csv-converter/", json=payload.model_dump())

    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]
    assert error_substring in response.json()["detail"]
