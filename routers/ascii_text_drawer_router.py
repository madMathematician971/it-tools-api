import logging

from fastapi import APIRouter, HTTPException, status
from pyfiglet import Figlet, FigletFont

from models.ascii_text_drawer_models import AsciiTextDrawerRequest, AsciiTextDrawerResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ascii-text-drawer", tags=["ASCII Text Drawer"])

# --- Main endpoint ---


@router.post("/", response_model=AsciiTextDrawerResponse)
async def generate_ascii_art(request: AsciiTextDrawerRequest):
    """Generate ASCII art from text using the specified font and alignment."""
    try:
        # Get available fonts
        available_fonts = FigletFont.getFonts()

        # If font not found, use default
        if request.font not in available_fonts:
            logger.warning(f"Font '{request.font}' not found, using 'standard'")
            selected_font = "standard"
        else:
            selected_font = request.font

        # Generate ASCII art with pyfiglet
        fig = Figlet(font=selected_font)
        ascii_art = fig.renderText(request.text)

        # Apply alignment if needed
        if request.alignment != "left":
            aligned_art = ""
            max_width = max(len(line) for line in ascii_art.split("\n"))

            for line in ascii_art.split("\n"):
                if request.alignment == "center":
                    padding = (max_width - len(line)) // 2
                    aligned_art += " " * padding + line + "\n"
                elif request.alignment == "right":
                    padding = max_width - len(line)
                    aligned_art += " " * padding + line + "\n"

            ascii_art = aligned_art

        return AsciiTextDrawerResponse(ascii_art=ascii_art, font_used=selected_font, alignment=request.alignment)

    except Exception as e:
        logger.error(f"Error generating ASCII art: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate ASCII art: {str(e)}"
        )
