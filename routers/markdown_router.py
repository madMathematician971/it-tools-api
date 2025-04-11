import markdown
from fastapi import APIRouter, HTTPException, status

from models.markdown_models import HtmlOutput, MarkdownInput

router = APIRouter(prefix="/api/markdown", tags=["Markdown"])


@router.post("/to-html", response_model=HtmlOutput)
async def markdown_to_html(payload: MarkdownInput):
    """Convert Markdown text to HTML."""
    try:
        # Basic conversion, extensions can be added for features like tables, fenced code blocks etc.
        # Example: extensions=['fenced_code', 'tables']
        html_content = markdown.markdown(payload.markdown_string, extensions=["fenced_code", "tables"])
        return {"html_string": html_content}
    except Exception as e:
        print(f"Error converting Markdown to HTML: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during Markdown conversion",
        )
