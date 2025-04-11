import xml.dom.minidom

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.xml_formatter_models import XmlInput, XmlOutput
from routers.xml_formatter_router import router as xml_formatter_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(xml_formatter_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test XML Formatting ---

# Sample XML strings
UNFORMATTED_XML = '<root><item id="1">Value 1</item><item id="2"><subitem>Value 2</subitem></item></root>'
PRETTY_XML_INDENT2_DECL = (
    xml.dom.minidom.parseString(UNFORMATTED_XML).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
)
# ElementTree formatting might differ slightly, used for non-preserving whitespace tests


@pytest.mark.parametrize(
    "input_xml, indent, preserve_whitespace, omit_declaration, encoding, expect_error, expected_substrings",
    [
        # Basic formatting (minidom)
        (UNFORMATTED_XML, "  ", True, False, "utf-8", False, ["<?xml", "<root>", "  <item", "Value 1", "</root>"]),
        # Different indent (minidom)
        (UNFORMATTED_XML, "\t", True, False, "utf-8", False, ["\t<item", "</item>"]),
        # Omit declaration (minidom)
        (UNFORMATTED_XML, "  ", True, True, "utf-8", False, ["<root>", "  <item"]),
        # Test minidom doesn't add declaration if omitted
        (UNFORMATTED_XML, "  ", True, True, "utf-8", False, []),  # Check absence below
        # Different encoding (minidom - check declaration)
        (UNFORMATTED_XML, "  ", True, False, "iso-8859-1", False, ['encoding="iso-8859-1"']),
        # Formatting without preserving whitespace (ElementTree)
        # ET formatting might slightly differ, check structure
        (UNFORMATTED_XML, "  ", False, False, "utf-8", False, ["<?xml", "<root>", "  <item", "</root>"]),
        # ET without declaration
        (UNFORMATTED_XML, "    ", False, True, "utf-8", False, ["<root>", "    <item", "</root>"]),
        # Test ET doesn't add declaration if omitted
        (UNFORMATTED_XML, "    ", False, True, "utf-8", False, []),  # Check absence below
        # Empty input
        ("", "  ", True, False, "utf-8", True, ["XML string cannot be empty"]),
        # Invalid XML (Test case updated to use self-closing tag as input)
        (
            "<root><item/></root>",
            "  ",
            True,  # preserve_whitespace = True -> uses minidom
            False,
            "utf-8",
            False,  # Expect no error
            ["<root>", "  <item/>", "</root>"],
        ),  # Self closing tag example
        ("<root><item>", "  ", True, False, "utf-8", True, ["Invalid XML"]),
    ],
)
@pytest.mark.asyncio
async def test_format_xml(
    client: TestClient,
    input_xml: str,
    indent: str,
    preserve_whitespace: bool,
    omit_declaration: bool,
    encoding: str,
    expect_error: bool,
    expected_substrings: list[str],
):
    """Test XML formatting with various options and inputs."""
    payload = XmlInput(
        xml=input_xml,
        indent=indent,
        preserve_whitespace=preserve_whitespace,
        omit_declaration=omit_declaration,
        encoding=encoding,
    )

    response = client.post("/api/xml-formatter/", json=payload.model_dump())

    if expect_error:
        if input_xml == "":
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert expected_substrings[0] in response.json()["detail"]
        else:  # Invalid XML error case
            assert response.status_code == status.HTTP_200_OK
            output = XmlOutput(**response.json())
            assert output.error is not None
            assert expected_substrings[0] in output.error
            assert output.formatted == ""
    else:
        assert response.status_code == status.HTTP_200_OK
        output = XmlOutput(**response.json())
        assert output.error is None
        assert isinstance(output.formatted, str)

        for sub in expected_substrings:
            assert sub in output.formatted

        # Check absence of declaration if omitted
        if omit_declaration:
            assert "<?xml" not in output.formatted
        # Check absence check for the specific case
        if input_xml == UNFORMATTED_XML and indent == "  " and preserve_whitespace is True and omit_declaration is True:
            assert "<?xml" not in output.formatted
        if (
            input_xml == UNFORMATTED_XML
            and indent == "    "
            and preserve_whitespace is False
            and omit_declaration is True
        ):
            assert "<?xml" not in output.formatted


# Test invalid input types (Pydantic validation)
@pytest.mark.asyncio
async def test_format_xml_invalid_type(client: TestClient):
    """Test providing invalid types for formatting options."""
    response = client.post(
        "/api/xml-formatter/",
        json={
            "xml": "<root/>",
            "indent": 2,  # Should be string
            "preserve_whitespace": "yes",  # Should be bool
            "omit_declaration": "maybe",  # Should be bool
            "encoding": 123,  # Should be string
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Update assertion for Pydantic v2 error message structure
    assert "input should be a valid" in response.text.lower()
