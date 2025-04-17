import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.lorem_generator import generate_lorem as generate_lorem_tool
from models.lorem_models import LoremInput, LoremOutput  # Keep models

router = APIRouter(prefix="/api/lorem", tags=["Lorem Ipsum"])
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=LoremOutput)
async def generate_lorem_endpoint(payload: LoremInput):
    """Generate Lorem Ipsum placeholder text using the MCP tool."""
    try:
        # Call the tool function
        result = generate_lorem_tool(
            lorem_type=payload.lorem_type.value, count=payload.count  # Pass enum value as string
        )

        # Check for errors from the tool
        if result.get("error"):
            logger.warning(f"Lorem Ipsum generation failed: {result['error']}")
            # Assume tool validation errors are 400 Bad Request
            if "Invalid lorem_type" in result["error"] or "Count must be" in result["error"]:
                status_code = status.HTTP_400_BAD_REQUEST
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR  # For unexpected tool errors
            raise HTTPException(
                status_code=status_code,
                detail=result["error"],
            )

        # Return successful result (tool output matches LoremOutput)
        return result

    except HTTPException:  # Re-raise
        raise
    except Exception as e:
        # Catch unexpected errors outside the tool call
        logger.error(f"Error in Lorem Ipsum endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during Lorem Ipsum generation",
        )
