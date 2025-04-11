import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

# Import models and router
from routers.list_converter_router import ListConverterInput, ListConverterOutput, ListFormat
from routers.list_converter_router import router as list_converter_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(list_converter_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test List Conversion ---


@pytest.mark.parametrize(
    "input_text, input_format, output_format, ignore_empty, trim_items, expected_result",
    [
        # Basic Conversions (comma <-> newline)
        ("a,b,c", ListFormat.COMMA_SEPARATED, ListFormat.NEWLINE_SEPARATED, True, True, "a\nb\nc"),
        ("a\nb\nc", ListFormat.NEWLINE_SEPARATED, ListFormat.COMMA_SEPARATED, True, True, "a,b,c"),
        # Space separated
        ("item1 item2 item3", ListFormat.SPACE_SEPARATED, ListFormat.COMMA_SEPARATED, True, True, "item1,item2,item3"),
        ("a,b,c", ListFormat.COMMA_SEPARATED, ListFormat.SPACE_SEPARATED, True, True, "a b c"),
        # Semicolon separated
        ("one;two;three", ListFormat.SEMICOLON_SEPARATED, ListFormat.NEWLINE_SEPARATED, True, True, "one\ntwo\nthree"),
        ("one\ntwo\nthree", ListFormat.NEWLINE_SEPARATED, ListFormat.SEMICOLON_SEPARATED, True, True, "one;two;three"),
        # Bullets / Numbered
        ("* item a\n* item b", ListFormat.BULLET_ASTERISK, ListFormat.COMMA_SEPARATED, True, True, "item a,item b"),
        ("- item a\n- item b", ListFormat.BULLET_HYPHEN, ListFormat.NUMBERED_DOT, True, True, "1. item a\n2. item b"),
        ("1. first\n2. second", ListFormat.NUMBERED_DOT, ListFormat.BULLET_ASTERISK, True, True, "* first\n* second"),
        ("1) first\n2) second", ListFormat.NUMBERED_PAREN, ListFormat.COMMA_SEPARATED, True, True, "first,second"),
        ("a,b,c", ListFormat.COMMA_SEPARATED, ListFormat.BULLET_HYPHEN, True, True, "- a\n- b\n- c"),
        ("a,b,c", ListFormat.COMMA_SEPARATED, ListFormat.NUMBERED_PAREN, True, True, "1) a\n2) b\n3) c"),
        # ignore_empty = True (default)
        ("a, ,b,,c,", ListFormat.COMMA_SEPARATED, ListFormat.NEWLINE_SEPARATED, True, True, "a\nb\nc"),
        ("a\n\nb\n\nc", ListFormat.NEWLINE_SEPARATED, ListFormat.COMMA_SEPARATED, True, True, "a,b,c"),
        (
            " * item a\n \n * item b\n ",
            ListFormat.BULLET_ASTERISK,
            ListFormat.COMMA_SEPARATED,
            True,
            True,
            "item a,item b",
        ),
        # ignore_empty = False
        (
            "a, ,b,,c,",
            ListFormat.COMMA_SEPARATED,
            ListFormat.NEWLINE_SEPARATED,
            False,
            True,
            "a\n\nb\n\nc\n",
        ),  # Note trailing empty item
        ("a\n\nb\n\nc", ListFormat.NEWLINE_SEPARATED, ListFormat.COMMA_SEPARATED, False, True, "a,,b,,c"),
        (
            "* item a\n\n* item b\n",
            ListFormat.BULLET_ASTERISK,
            ListFormat.COMMA_SEPARATED,
            False,
            True,
            "item a,,item b",
        ),  # Includes empty lines as items
        # trim_items = True (default)
        (" a , b , c ", ListFormat.COMMA_SEPARATED, ListFormat.NEWLINE_SEPARATED, True, True, "a\nb\nc"),
        ("\n item1 \n item2 \n ", ListFormat.NEWLINE_SEPARATED, ListFormat.COMMA_SEPARATED, True, True, "item1,item2"),
        (" * item a \n * item b ", ListFormat.BULLET_ASTERISK, ListFormat.COMMA_SEPARATED, True, True, "item a,item b"),
        # trim_items = False
        (" a , b , c ", ListFormat.COMMA_SEPARATED, ListFormat.NEWLINE_SEPARATED, True, False, " a \n b \n c "),
        (
            "\n item1 \n item2 \n ",
            ListFormat.NEWLINE_SEPARATED,
            ListFormat.COMMA_SEPARATED,
            True,
            False,
            " item1 , item2 , ",
        ),
        (
            " * item a \n * item b ",
            ListFormat.BULLET_ASTERISK,
            ListFormat.COMMA_SEPARATED,
            True,
            False,
            " item a, item b",
        ),
        # Empty input
        ("", ListFormat.COMMA_SEPARATED, ListFormat.NEWLINE_SEPARATED, True, True, ""),
    ],
)
@pytest.mark.asyncio
async def test_list_converter_success(
    client: TestClient,
    input_text: str,
    input_format: ListFormat,
    output_format: ListFormat,
    ignore_empty: bool,
    trim_items: bool,
    expected_result: str,
):
    """Test successful list conversions between various formats and options."""
    payload = ListConverterInput(
        input_text=input_text,
        input_format=input_format,
        output_format=output_format,
        ignore_empty=ignore_empty,
        trim_items=trim_items,
    )
    response = client.post("/api/list-converter/convert", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = ListConverterOutput(**response.json())
    assert output.result == expected_result


# No specific failure cases defined beyond Pydantic validation or potential 500s,
# as the parsing/formatting logic is designed to handle most inputs gracefully.
# Could add tests for invalid enum values if Pydantic doesn't catch them, but it should.
