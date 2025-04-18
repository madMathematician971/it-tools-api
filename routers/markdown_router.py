import logging

from fastapi import APIRouter, HTTPException, status

# Import the MCP tool
from mcp_server.tools.markdown_processor import render_markdown
from models.markdown_models import HtmlOutput, MarkdownInput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/markdown", tags=["Markdown"])


@router.post("/to-html", response_model=HtmlOutput)
async def markdown_to_html_endpoint(payload: MarkdownInput):
    """Convert Markdown text to HTML using the MCP tool."""
    try:
        # Call the MCP tool
        result = await render_markdown(markdown_string=payload.markdown_string)

        # Handle potential errors from the tool
        if result.get("error"):
            logger.warning(f"Markdown tool returned error: {result['error']}")
            # Map tool error to a user-friendly message or appropriate HTTP status
            if "Input must be a string" in result["error"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: Markdown data must be a string.",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Internal server error during Markdown conversion: {result['error']}",
                )

        html_content = result.get("html_string")
        if html_content is None:
            # Should ideally be caught by the error check above, but handle defensively
            logger.error("Markdown tool returned None for html_string without error.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error: Unexpected response from conversion tool.",
            )

        return {"html_string": html_content}

    except HTTPException as http_exc:
        # Re-raise HTTPException to let FastAPI handle it
        raise http_exc
    except Exception as e:
        logger.exception(f"Unexpected error in markdown_to_html endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal server error occurred.",
        )
