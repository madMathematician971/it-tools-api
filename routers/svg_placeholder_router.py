import base64
import logging

from fastapi import APIRouter

from models.svg_placeholder_models import SvgInput, SvgOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/svg-placeholder", tags=["SVG Placeholder Generator"])


@router.post("/", response_model=SvgOutput)
async def generate_svg_placeholder(input_data: SvgInput):
    """Generate an SVG placeholder image with specified dimensions, colors, and text."""
    try:
        width = input_data.width
        height = input_data.height
        bg_color = input_data.bg_color
        text_color = input_data.text_color
        text = input_data.text
        font_family = input_data.font_family
        font_size = input_data.font_size

        # Auto-calculate font size if not provided
        if not font_size:
            # Simple heuristic: font size proportional to smaller dimension
            font_size = min(width, height) // 5
            if font_size < 10:
                font_size = 10  # Minimum size

        # Construct SVG content
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">"""
        svg_content += f'<rect fill="{bg_color}" width="{width}" height="{height}"/>'

        # Add text if provided
        if text:
            # Center text
            text_x = width / 2
            text_y = height / 2
            svg_content += (
                f'<text x="{text_x}" y="{text_y}" '
                f'font-family="{font_family}" font-size="{font_size}" '
                f'fill="{text_color}" text-anchor="middle" dy=".3em">'
                f"{text}"
                f"</text>"
            )

        svg_content += "</svg>"

        # Create Data URI
        svg_data_uri = f"data:image/svg+xml;base64,{base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')}"

        return SvgOutput(svg=svg_content, data_uri=svg_data_uri)

    except ValueError as ve:
        # Raised by validators
        return SvgOutput(svg="", data_uri="", error=f"Invalid input: {str(ve)}")
    except Exception as e:
        logger.error(f"Error generating SVG placeholder: {e}", exc_info=True)
        return SvgOutput(svg="", data_uri="", error=f"Failed to generate SVG: {str(e)}")
