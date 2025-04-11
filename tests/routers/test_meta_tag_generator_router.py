import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.meta_tag_generator_models import MetaTagInput, MetaTagOutput
from routers.meta_tag_generator_router import router as meta_tag_generator_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(meta_tag_generator_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Meta Tag Generation ---

# Basic input data
basic_data = {
    "title": "Test Title",
    "description": "Test Description",
    # Use defaults for most other fields
}

# Full input data
full_data = {
    "title": "Full Test Title <Tag>",
    "description": "A more & detailed test description.",
    "keywords": "test, meta, tags",
    "author": "Test Author",
    "language": "en-GB",
    "robots": "noindex, nofollow",
    "viewport": "width=device-width, initial-scale=0.8",
    "og_type": "article",
    "og_url": "https://example.com/article",
    "og_image": "https://example.com/image.jpg",
    "twitter_card": "summary_large_image",
    "twitter_site": "@example",
}


@pytest.mark.parametrize(
    "input_payload_dict, expected_tags_count, expected_html_substrings",
    [
        # Basic test with minimal input
        (
            basic_data,
            6,  # title, desc, lang, robots, viewport, og:title, og:desc, og:type, tw:title, tw:desc, tw:card - depends on defaults
            [
                "<title>Test Title</title>",
                '<meta name="description" content="Test Description" />',
                '<meta name="robots" content="index, follow" />',  # Default
                '<meta name="viewport" content="width=device-width, initial-scale=1.0" />',  # Default
                '<meta property="og:title" content="Test Title" />',
                '<meta property="og:description" content="Test Description" />',
                '<meta property="og:type" content="website" />',  # Default
                '<meta property="twitter:title" content="Test Title" />',
                '<meta property="twitter:description" content="Test Description" />',
                '<meta property="twitter:card" content="summary" />',  # Default
            ],
        ),
        # Test with all fields provided
        (
            full_data,
            12,  # All fields present
            [
                "<title>Full Test Title &lt;Tag&gt;</title>",
                '<meta name="description" content="A more &amp; detailed test description." />',
                '<meta name="keywords" content="test, meta, tags" />',
                '<meta name="author" content="Test Author" />',
                '<meta name="language" content="en-GB" />',
                '<meta name="robots" content="noindex, nofollow" />',
                '<meta name="viewport" content="width=device-width, initial-scale=0.8" />',
                '<meta property="og:title" content="Full Test Title &lt;Tag&gt;" />',
                '<meta property="og:description" content="A more &amp; detailed test description." />',
                '<meta property="og:type" content="article" />',
                '<meta property="og:url" content="https://example.com/article" />',
                '<meta property="og:image" content="https://example.com/image.jpg" />',
                '<meta property="twitter:title" content="Full Test Title &lt;Tag&gt;" />',
                '<meta property="twitter:description" content="A more &amp; detailed test description." />',
                '<meta property="twitter:card" content="summary_large_image" />',
                '<meta property="twitter:site" content="@example" />',
            ],
        ),
        # Test HTML escaping in content
        (
            {"title": "Title with <script>", "description": "Desc & stuff"},
            6,  # title, desc, lang, robots, viewport, og:title, og:desc, og:type, tw:title, tw:desc, tw:card - depends on defaults
            [
                "<title>Title with &lt;script&gt;</title>",
                '<meta name="description" content="Desc &amp; stuff" />',
                '<meta property="og:title" content="Title with &lt;script&gt;" />',
                '<meta property="og:description" content="Desc &amp; stuff" />',
            ],
        ),
    ],
)
@pytest.mark.asyncio
async def test_generate_meta_tags_success(
    client: TestClient, input_payload_dict: dict, expected_tags_count: int, expected_html_substrings: list[str]
):
    """Test successful generation of meta tags with various inputs."""
    payload = MetaTagInput(**input_payload_dict)
    response = client.post("/api/meta-tag-generator/", json=payload.model_dump(exclude_unset=True))

    assert response.status_code == status.HTTP_200_OK
    output = MetaTagOutput(**response.json())

    assert isinstance(output.html, str)
    assert isinstance(output.tags, dict)

    # Check expected number of tags generated in the dictionary (adjust based on model defaults)
    # This is tricky as defaults fill missing values. Check presence instead.
    # assert len(output.tags) >= expected_tags_count

    # Check that essential tags from input are present in the tags dict
    for key, value in input_payload_dict.items():
        # Map input keys to potential output keys (e.g., title maps to title, og:title, twitter:title)
        related_keys = [key, f"og:{key}", f"twitter:{key}"]
        found = False
        for r_key in related_keys:
            if r_key in output.tags and output.tags[r_key] == value:
                found = True
                break
        # Special case for title tag vs title attribute
        if key == "title":
            assert output.tags["title"] == value
            assert output.tags["og:title"] == value
            assert output.tags["twitter:title"] == value
        # Other straightforward keys
        elif key in output.tags:
            assert output.tags[key] == value

    # Check for presence and escaping of substrings in the generated HTML
    assert isinstance(output.html, str)
    for substring in expected_html_substrings:
        assert substring in output.html


# Test with missing required fields (should be caught by Pydantic)
@pytest.mark.asyncio
async def test_generate_meta_tags_missing_required(client: TestClient):
    """Test request with missing required fields like title or description."""
    response = client.post("/api/meta-tag-generator/", json={})  # Missing title and description
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_json = response.json()
    assert any("title" in err["loc"] for err in response_json["detail"])
    assert any("description" in err["loc"] for err in response_json["detail"])
