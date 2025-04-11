import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

# Import models from models.text_diff_models
from models.text_diff_models import DiffFormat, TextDiffInput, TextDiffOutput

# Remove unused imports from router
# from routers.text_diff_router import DiffFormat, TextDiffInput
from routers.text_diff_router import router as text_diff_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(text_diff_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Text Diff Generation ---

TEXT_A = "This is line 1.\nThis is line 2.\nThis is line 3."
TEXT_B = "This is line 1.\nThis is UPDATED line 2.\nThis is line 3."
TEXT_A_WHITESPACE = "  line one  \n line two "
TEXT_B_WHITESPACE = "line one\nline two"


@pytest.mark.parametrize(
    "text_a, text_b, output_format, context_lines, ignore_whitespace, expected_substrings",
    [
        # Unified format
        (
            TEXT_A,
            TEXT_B,
            DiffFormat.UNIFIED,
            3,
            False,
            ["--- text1", "+++ text2", "-This is line 2.", "+This is UPDATED line 2."],
        ),
        (
            TEXT_A,
            TEXT_B,
            DiffFormat.UNIFIED,
            0,
            False,
            ["-This is line 2.", "+This is UPDATED line 2."],
        ),  # Zero context
        # Ndiff format
        (TEXT_A, TEXT_B, DiffFormat.NDIFF, 3, False, ["- This is line 2.", "+ This is UPDATED line 2."]),
        # HTML format - Check for key elements (table, original line, change)
        (TEXT_A, TEXT_B, DiffFormat.HTML, 3, False, ["<table", "This&nbsp;is&nbsp;line&nbsp;2.", "UPDATED"]),
        # Ignore whitespace
        (
            TEXT_A_WHITESPACE,
            TEXT_B_WHITESPACE,
            DiffFormat.UNIFIED,
            3,
            True,
            [],
        ),  # Expect no diff when ignoring whitespace
        (
            TEXT_A_WHITESPACE,
            TEXT_B_WHITESPACE,
            DiffFormat.UNIFIED,
            3,
            False,
            ["-  line one", "+line one", "- line two", "+line two"],
        ),  # Expect diff when not ignoring
        # No difference
        (TEXT_A, TEXT_A, DiffFormat.UNIFIED, 3, False, []),  # Empty diff for identical text
    ],
)
@pytest.mark.asyncio
async def test_generate_text_diff_success(
    client: TestClient,
    text_a: str,
    text_b: str,
    output_format: DiffFormat,
    context_lines: int,
    ignore_whitespace: bool,
    expected_substrings: list[str],
):
    """Test successful diff generation in various formats and options."""
    payload = TextDiffInput(
        text1=text_a,
        text2=text_b,
        output_format=output_format,
        context_lines=context_lines,
        ignore_whitespace=ignore_whitespace,
    )
    response = client.post("/api/text-diff/", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    # Validate using the imported TextDiffOutput
    try:
        output = TextDiffOutput(**response.json())
    except Exception as e:
        pytest.fail(f"Response validation failed for diff output: {e}\nResponse: {response.json()}")

    assert output.error is None
    assert output.format_used == output_format.value
    assert isinstance(output.diff, str)

    if not expected_substrings:  # Handle case where no diff is expected
        assert not output.diff.strip()
    else:
        for sub in expected_substrings:
            assert sub.lower() in output.diff.lower()


@pytest.mark.parametrize(
    "payload_update, error_substring",
    [
        ({"output_format": "invalid"}, "Input should be 'unified', 'context', 'html' or 'ndiff'"),
        ({"context_lines": -1}, "Input should be greater than or equal to 0"),
    ],
)
@pytest.mark.asyncio
async def test_generate_text_diff_invalid_input(client: TestClient, payload_update: dict, error_substring: str):
    """Test diff generation with invalid input values (caught by Pydantic)."""
    base_payload = {
        "text1": "line1",
        "text2": "line2",
        "output_format": DiffFormat.UNIFIED,
        "context_lines": 3,
        "ignore_whitespace": False,
    }
    invalid_payload_dict = {**base_payload, **payload_update}

    response = client.post("/api/text-diff/", json=invalid_payload_dict)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_json = response.json()
    assert "detail" in response_json
    assert isinstance(response_json["detail"], list)
    assert len(response_json["detail"]) > 0
    assert "msg" in response_json["detail"][0]
    assert error_substring.lower() in response_json["detail"][0]["msg"].lower()
