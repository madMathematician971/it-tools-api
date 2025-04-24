import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.meta_tag_generator import generate_meta_tags
from models.meta_tag_generator_models import MetaTagInput, MetaTagOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meta-tag-generator", tags=["Meta Tag Generator"])


@router.post("/", response_model=MetaTagOutput)
async def generate_meta_tags(input_data: MetaTagInput):
    """Generate HTML meta tags based on provided input data using the MCP tool."""
    try:
        result_dict = generate_meta_tags(**input_data.model_dump())

        if result_dict["error"]:
            logger.error(f"MCP tool failed: {result_dict['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to generate meta tags: {result_dict['error']}",
            )

        tool_result = result_dict["result"]
        if tool_result:
            return MetaTagOutput(html=tool_result["html"], tags=tool_result["tags"])
        else:
            logger.error("MCP tool returned no result and no error.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while generating meta tags.",
            )

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly
        raise http_exc
    except Exception as e:
        # Catch any other unexpected errors during the process
        logger.error(f"Error calling generate_meta_tags tool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate meta tags: {str(e)}"
        )
