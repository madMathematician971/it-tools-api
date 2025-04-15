import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.json_diff import json_diff
from models.json_diff_models import JsonDiffInput, JsonDiffOutput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/json-diff", tags=["JSON Diff"])


@router.post("/", response_model=JsonDiffOutput)
async def generate_json_diff_endpoint(input_data: JsonDiffInput):
    """Compare two JSON objects and show the differences."""
    try:
        # Call the tool function
        result = json_diff(
            json1=input_data.json1,
            json2=input_data.json2,
            ignore_order=input_data.ignore_order,
            output_format=input_data.output_format,
        )

        # Check for errors returned by the tool
        if result.get("error"):
            logger.info(f"JSON diff failed: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        # Return successful result from the tool
        # The result dict structure from the tool matches JsonDiffOutput
        return result

    # Keep the general exception handler for unexpected errors
    except HTTPException:  # Re-raise HTTPException if already raised
        raise
    except Exception as e:
        logger.error(f"Error in JSON diff endpoint: {e}", exc_info=True)
        # Return error structure expected by the response model for 500 errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during JSON diff generation: {str(e)}",
        )
