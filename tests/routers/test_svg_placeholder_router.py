import base64
import re

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.svg_placeholder_models import SvgInput, SvgOutput
from routers.svg_placeholder_router import router as svg_placeholder_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(svg_placeholder_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test SVG Placeholder Generation ---


@pytest.mark.parametrize(
    "width, height, bg_color, text_color, text, font_family, font_size, expected_text_present, expected_auto_font_size",
    [
        # Basic case
        (100, 50, "#cccccc", "#333333", "100x50", "sans-serif", None, True, True),
        # No text
        (50, 50, "#eee", "#aaa", "", "Verdana", None, False, True),  # Auto font size calculated but not used
        # Different dimensions
        (30, 150, "#aabbcc", "#112233", "Tall", "sans-serif", None, True, True),
        # Small dimensions leading to minimum font size
        (20, 10, "#ddd", "#111", "tiny", "sans-serif", None, True, True),
    ],
)
@pytest.mark.asyncio
async def test_generate_svg_placeholder_success(
    client: TestClient,
    width: int,
    height: int,
    bg_color: str,
    text_color: str,
    text: str,
    font_family: str,
    font_size: int | None,
    expected_text_present: bool,
    expected_auto_font_size: bool,
):
    """Test successful generation of SVG placeholders with various options."""
    payload_dict = {
        "width": width,
        "height": height,
        "bg_color": bg_color,
        "text_color": text_color,
        "text": text,
        "font_family": font_family,
        "font_size": font_size,
    }
    # Pydantic handles optional font_size being None
    payload = SvgInput(**{k: v for k, v in payload_dict.items() if v is not None})

    response = client.post("/api/svg-placeholder/", json=payload.model_dump(exclude_unset=True))

    assert response.status_code == status.HTTP_200_OK
    output = SvgOutput(**response.json())

    assert output.error is None
    assert isinstance(output.svg, str)
    assert isinstance(output.data_uri, str)

    # Validate SVG structure and attributes
    assert f'width="{width}"' in output.svg
    assert f'height="{height}"' in output.svg
    assert f'fill="{bg_color}"' in output.svg

    if expected_text_present:
        assert f'fill="{text_color}"' in output.svg
        assert f'font-family="{font_family}"' in output.svg
        assert f">{text}</text>" in output.svg
        # Check font size
        font_size_match = re.search(r'font-size="(\d+)" ', output.svg)
        assert font_size_match is not None
        actual_font_size = int(font_size_match.group(1))
        if font_size:
            assert actual_font_size == font_size
        else:  # Auto-calculated
            expected_calculated_fs = max(10, min(width, height) // 5)
            assert actual_font_size == expected_calculated_fs
    else:
        assert "<text" not in output.svg

    # Validate Data URI
    assert output.data_uri.startswith("data:image/svg+xml;base64,")
    try:
        # Decode base64 part and check if it matches the SVG string
        base64_content = output.data_uri.split(",", 1)[1]
        decoded_svg = base64.b64decode(base64_content).decode("utf-8")
        assert decoded_svg == output.svg
    except Exception:
        pytest.fail("Data URI validation failed (could not decode or mismatch)")


@pytest.mark.parametrize(
    "payload_update, error_substring",
    [
        ({"width": 0}, "Input should be greater than or equal to 1"),
        ({"height": -10}, "Input should be greater than or equal to 1"),
        ({"bg_color": "invalid-color"}, "Invalid hex color format"),
        ({"text_color": "#12345"}, "Invalid hex color format"),
        ({"bg_color": "blue"}, "Invalid hex color format"),
        ({"text_color": "red"}, "Invalid hex color format"),
        ({"font_size": 0}, "Input should be greater than or equal to 1"),
    ],
)
@pytest.mark.asyncio
async def test_generate_svg_placeholder_invalid_input(client: TestClient, payload_update: dict, error_substring: str):
    """Test SVG generation with invalid input values (caught by Pydantic)."""
    base_payload = {
        "width": 100,
        "height": 50,
        "bg_color": "#eee",
        "text_color": "#111",
        "text": "Valid",
    }
    invalid_payload_dict = {**base_payload, **payload_update}

    response = client.post("/api/svg-placeholder/", json=invalid_payload_dict)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert error_substring in str(response.json())  # Check Pydantic error detail
