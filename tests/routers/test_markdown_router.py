import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.markdown_models import HtmlOutput, MarkdownInput
from routers.markdown_router import router as markdown_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(markdown_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Markdown to HTML Conversion ---


@pytest.mark.parametrize(
    "markdown_input, expected_html_substrings",
    [
        ("# Heading 1", ["<h1>Heading 1</h1>"]),
        ("## Heading 2", ["<h2>Heading 2</h2>"]),
        ("Some *italic* and **bold** text.", ["<em>italic</em>", "<strong>bold</strong>"]),
        ("`inline code`", ["<code>inline code</code>"]),
        ("A list:\n\n* Item 1\n* Item 2", ["<ul>", "<li>Item 1</li>", "<li>Item 2</li>", "</ul>"]),
        ("1. First\n2. Second", ["<ol>", "<li>First</li>", "<li>Second</li>", "</ol>"]),
        ("[A link](http://example.com)", ['<a href="http://example.com">A link</a>']),
        ("> Blockquote", ["<blockquote>", "<p>Blockquote</p>", "</blockquote>"]),
        # Test extensions (fenced code, tables)
        ("```python\nprint('hello')\n```", ["<pre><code class=\"language-python\">print('hello')\n</code></pre>"]),
        (
            "| Header | Column |\n|---|---|\n| Cell | Data |",
            ["<table>", "<thead>", "<th>Header</th>", "</thead>", "<tbody>", "<td>Cell</td>", "</tbody>", "</table>"],
        ),
        ("", [""]),  # Empty input should produce empty or minimal output
    ],
)
@pytest.mark.asyncio
async def test_markdown_to_html_success(client: TestClient, markdown_input: str, expected_html_substrings: list[str]):
    """Test successful conversion of various Markdown elements to HTML."""
    payload = MarkdownInput(markdown_string=markdown_input)
    response = client.post("/api/markdown/to-html", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = HtmlOutput(**response.json())

    assert isinstance(output.html_string, str)
    if not expected_html_substrings or expected_html_substrings == [""]:
        assert output.html_string == ""
    else:
        for substring in expected_html_substrings:
            assert substring in output.html_string


# Test with non-string input (should be caught by Pydantic)
@pytest.mark.asyncio
async def test_markdown_to_html_invalid_input_type(client: TestClient):
    """Test providing invalid type for the markdown string."""
    response = client.post("/api/markdown/to-html", json={"markdown_string": 123})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
