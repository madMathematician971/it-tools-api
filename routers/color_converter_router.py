import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.color_converter import convert_color
from models.color_converter_models import ColorConvertInput, ColorConvertOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/color", tags=["Color Converter"])


@router.post("/convert", response_model=ColorConvertOutput)
async def color_convert_endpoint(payload: ColorConvertInput):
    """Convert color between different formats using the tool."""
    try:
        result = convert_color(input_color=payload.input_color, target_format=payload.target_format)

        if result["error"]:
            tool_error_msg = result["error"]
            # Check for specific user-facing errors from the tool
            if (
                "Could not parse input color" in tool_error_msg
                or "Input color string cannot be empty" in tool_error_msg
            ):
                logger.warning(f"Invalid color input/parse error: {payload.input_color} - Tool Error: {tool_error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    # Return the specific error from the tool
                    detail=tool_error_msg,
                )
            if "Unsupported target_format" in tool_error_msg:
                logger.warning(f"Unsupported target format requested: {payload.target_format}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    # Return the specific error from the tool
                    detail=tool_error_msg,
                )

            # Log other internal tool errors and return a generic 500
            logger.error(f"Color converter tool returned an unexpected internal error: {tool_error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during color conversion",  # Generic message for internal errors
            )

        # The dictionary returned by the tool matches the fields expected by ColorConvertOutput
        return ColorConvertOutput(**result)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        # Catch any unexpected exceptions during the tool call or processing
        logger.error(f"Unexpected error in /color/convert endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during color conversion to {payload.target_format}",
        )
