import logging

from fastapi import APIRouter, HTTPException, status

# Import the tool function
from mcp_server.tools.list_converter import convert_list as convert_list_tool

# Import models from the models directory
from models.list_converter_models import ListConverterInput, ListConverterOutput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/list-converter", tags=["List Converter"])


@router.post(
    "/convert",
    response_model=ListConverterOutput,
    summary="Convert text between different list formats",
)
async def convert_list_endpoint(payload: ListConverterInput):
    """Converts list items from one text format (e.g., comma-separated) to another (e.g., bullet points)."""
    try:
        # Call the tool function
        result = convert_list_tool(
            input_text=payload.input_text,
            input_format=payload.input_format,  # Pass string directly
            output_format=payload.output_format,  # Pass string directly
            ignore_empty=payload.ignore_empty,
            trim_items=payload.trim_items,
        )

        # Check for errors from the tool
        if result.get("error"):
            logger.info(f"List conversion failed: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        # Return successful result from the tool
        # The result dict structure from the tool matches ListConverterOutput
        return result

    # Keep general exception handler
    except HTTPException:  # Re-raise
        raise
    except Exception as e:
        logger.error(
            f"Error converting list from {payload.input_format} to {payload.output_format}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during list conversion: {str(e)}",
        )
