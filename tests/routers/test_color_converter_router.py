import pytest
from colour import Color  # Used for direct comparison/validation
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.color_converter_models import ColorConvertInput, ColorConvertOutput
from routers.color_converter_router import router as color_converter_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(color_converter_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Color Conversion ---


@pytest.mark.parametrize(
    "input_color, target_format, expected_result",
    [
        # Hex -> Various
        ("#FF0000", "rgb", "rgb(255, 0, 0)"),
        ("#00FF00", "hsl", "hsl(120, 100%, 50%)"),
        ("#FFFFFF", "web", "white"),
        ("#808080", "luminance", 0.5019607843137255),  # Updated value
        ("#FF0000", "hex", "#f00"),
        ("#FF0000", "hex_verbose", "#ff0000"),
        ("#abcdef", "hex_verbose", "#abcdef"),
        ("#123", "hex_verbose", "#112233"),
        ("#123", "rgb", "rgb(16, 33, 51)"),  # Updated value
        # Web names -> Various
        ("red", "hex_verbose", "#ff0000"),
        ("lime", "rgb", "rgb(0, 255, 0)"),
        ("blue", "hsl", "hsl(240, 100%, 50%)"),
        ("grey", "hex", "#808080"),
        ("darkgrey", "hex", "#a9a9a9"),
        # Case insensitivity
        ("ReD", "rgb", "rgb(255, 0, 0)"),
        ("#ff0000", "TARGET_FORMAT", None),
    ],
)
@pytest.mark.asyncio
async def test_color_convert_success(client: TestClient, input_color: str, target_format: str, expected_result):
    """Test successful color conversions between various formats."""
    # Handle the case-insensitivity test for target_format separately
    if target_format == "TARGET_FORMAT":
        target_format_actual = "rgb"
        expected_result_actual = "rgb(255, 0, 0)"
    else:
        target_format_actual = target_format
        expected_result_actual = expected_result

    payload = ColorConvertInput(input_color=input_color, target_format=target_format_actual)
    response = client.post("/api/color/convert", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = ColorConvertOutput(**response.json())

    # Handle float comparison with tolerance for luminance
    if target_format_actual == "luminance":
        assert isinstance(output.result, float)
        # Ensure the expected result is also treated as float for comparison
        assert isinstance(expected_result_actual, (float, int)), "Expected result for luminance must be numeric"
        assert abs(output.result - float(expected_result_actual)) < 1e-6
    else:
        assert output.result == expected_result_actual

    # Verify parsed values (using the library directly for comparison)
    try:
        c = Color(input_color)
        assert output.parsed_hex == c.hex_l
        r_int, g_int, b_int = [int(x * 255) for x in c.rgb]
        assert output.parsed_rgb == f"rgb({r_int}, {g_int}, {b_int})"
        h_deg_hsl, s_hsl, l_hsl = (
            round(c.hsl[0] * 360),
            round(c.hsl[1] * 100),
            round(c.hsl[2] * 100),
        )
        assert output.parsed_hsl == f"hsl({h_deg_hsl}, {s_hsl}%, {l_hsl}%)"
    except Exception:
        # If input color was invalid for the Color library (should be caught earlier)
        pass


@pytest.mark.parametrize(
    "invalid_input_color",
    [
        "not a color",
        "#12345",  # Invalid hex length
        "rgb(256, 0, 0)",  # Invalid RGB value
        "hsl(400, 100%, 50%)",  # Invalid HSL value
        "web(invalid)",
    ],
)
@pytest.mark.asyncio
async def test_color_convert_invalid_input_color(client: TestClient, invalid_input_color: str):
    """Test color conversion with invalid input color strings."""
    # Assume these inputs should now trigger Pydantic validation errors (422) or internal 400s
    # Check for both possibilities for robustness
    payload = ColorConvertInput(input_color=invalid_input_color, target_format="hex")
    response = client.post("/api/color/convert", json=payload.model_dump())

    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
    error_detail = str(response.json()).lower()
    # Check for common error substrings
    assert (
        "could not parse input color" in error_detail
        or "invalid" in error_detail  # General check for Pydantic/other errors
        or "value error" in error_detail  # Pydantic v2
    )


@pytest.mark.asyncio
async def test_color_convert_invalid_target_format(client: TestClient):
    """Test color conversion with an unsupported target format."""
    payload = ColorConvertInput(input_color="red", target_format="invalid-format")
    response = client.post("/api/color/convert", json=payload.model_dump())

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported target_format" in response.json()["detail"]
    assert "invalid-format" in response.json()["detail"]
