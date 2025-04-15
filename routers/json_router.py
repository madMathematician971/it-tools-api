import logging

from fastapi import APIRouter, HTTPException, status

# Import tool functions
from mcp_server.tools.json_formatter import format_json as format_json_tool
from mcp_server.tools.json_formatter import minify_json as minify_json_tool
from models.json_models import JsonFormatInput, JsonOutput, JsonTextInput

router = APIRouter(prefix="/api/json", tags=["JSON"])
logger = logging.getLogger(__name__)


@router.post("/format", response_model=JsonOutput)
async def format_json_endpoint(payload: JsonFormatInput):
    """Format (pretty-print) a JSON string."""
    try:
        # Call the tool function
        result = format_json_tool(json_string=payload.json_string, indent=payload.indent, sort_keys=payload.sort_keys)
        # Check for errors from the tool
        if result.get("error"):
            logger.info(f"JSON formatting failed: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )
        return result  # Result dict matches JsonOutput model
    except HTTPException:  # Re-raise
        raise
    except Exception as e:
        logger.error(f"Error formatting JSON: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during JSON formatting",
        )


@router.post("/minify", response_model=JsonOutput)
async def minify_json_endpoint(payload: JsonTextInput):
    """Minify a JSON string (remove unnecessary whitespace)."""
    try:
        # Call the tool function
        result = minify_json_tool(json_string=payload.json_string)
        # Check for errors from the tool
        if result.get("error"):
            logger.info(f"JSON minification failed: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )
        return result  # Result dict matches JsonOutput model
    except HTTPException:  # Re-raise
        raise
    except Exception as e:
        logger.error(f"Error minifying JSON: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during JSON minification",
        )
