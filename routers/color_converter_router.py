from colour import Color
from fastapi import APIRouter, HTTPException, status

from models.color_converter_models import ColorConvertInput, ColorConvertOutput

router = APIRouter(prefix="/api/color", tags=["Color Converter"])


@router.post("/convert", response_model=ColorConvertOutput)
async def color_convert(payload: ColorConvertInput):
    """Convert color between different formats (hex, rgb, hsl, hsv, web names)."""
    try:
        c = Color(payload.input_color)
    except Exception as e:
        print(f"Error parsing input color '{payload.input_color}': {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse input color: '{payload.input_color}'",
        )

    target = payload.target_format.lower()
    result: str | float  # Use | for Union in type hint

    try:
        if target == "hex":
            result = c.hex
        elif target == "hex_verbose":
            result = c.hex_l
        elif target == "rgb":
            r, g, b = [int(x * 255) for x in c.rgb]
            result = f"rgb({r}, {g}, {b})"
        elif target == "rgb_fraction":
            result = str(c.rgb)
        elif target == "hsl":
            h_deg = round(c.hsl[0] * 360)
            s, l_ = [round(x * 100) for x in c.hsl[1:]]
            result = f"hsl({h_deg}, {s}%, {l_}%)"
        elif target == "hsv":
            h_deg = round(c.hsv[0] * 360)
            s, v = [round(x * 100) for x in c.hsv[1:]]
            result = f"hsv({h_deg}, {s}%, {v}%)"
        elif target == "web":
            result = c.web
        elif target == "luminance":
            result = c.luminance
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported target_format: '{payload.target_format}'",
            )

        parsed_hex = c.hex_l
        r_int, g_int, b_int = [int(x * 255) for x in c.rgb]
        parsed_rgb = f"rgb({r_int}, {g_int}, {b_int})"
        h_deg_hsl, s_hsl, l_hsl = (
            round(c.hsl[0] * 360),
            round(c.hsl[1] * 100),
            round(c.hsl[2] * 100),
        )
        parsed_hsl = f"hsl({h_deg_hsl}, {s_hsl}%, {l_hsl}%)"

        return {
            "result": result,
            "input_color": payload.input_color,
            "target_format": payload.target_format,
            "parsed_hex": parsed_hex,
            "parsed_rgb": parsed_rgb,
            "parsed_hsl": parsed_hsl,
        }

    except Exception as e:
        print(f"Error converting color '{payload.input_color}' to '{target}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during color conversion to {target}",
        )
