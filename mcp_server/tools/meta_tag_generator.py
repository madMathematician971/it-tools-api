"""
Meta Tag Generator tool for MCP server.
"""

import html
import logging
from typing import Any

from mcp_server import mcp_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@mcp_app.tool()
def generate_meta_tags(
    title: str,
    description: str,
    keywords: str = "",
    author: str = "",
    language: str = "en",
    robots: str = "index, follow",
    viewport: str = "width=device-width, initial-scale=1.0",
    og_type: str = "website",
    og_url: str = "",
    og_image: str = "",
    twitter_card: str = "summary",
    twitter_site: str = "",
) -> dict[str, Any]:
    """
    Generate HTML meta tags based on provided input data.

    Args:
        title: Title of the page
        description: Description of the page content
        keywords: Comma-separated keywords
        author: Author of the page
        language: Content language (ISO code)
        robots: Robots directive
        viewport: Viewport settings
        og_type: OpenGraph type
        og_url: OpenGraph URL
        og_image: OpenGraph image URL
        twitter_card: Twitter card type
        twitter_site: Twitter site username

    Returns:
        A dictionary containing:
            result: Dictionary containing 'html' (generated tags string) and 'tags' (dict of tags)
            error: Optional error message
    """
    try:
        # Initialize dictionary to store tags
        tags = {}

        # Generate basic meta tags
        tags["title"] = title
        tags["description"] = description

        if keywords:
            tags["keywords"] = keywords

        if author:
            tags["author"] = author

        tags["language"] = language
        tags["robots"] = robots
        tags["viewport"] = viewport

        # Generate Open Graph tags
        tags["og:title"] = title
        tags["og:description"] = description
        tags["og:type"] = og_type

        if og_url:
            tags["og:url"] = og_url

        if og_image:
            tags["og:image"] = og_image

        # Generate Twitter Card tags
        tags["twitter:title"] = title
        tags["twitter:description"] = description
        tags["twitter:card"] = twitter_card

        if twitter_site:
            tags["twitter:site"] = twitter_site

        # Generate HTML
        html_tags = []
        html_tags.append(f"<title>{html.escape(title)}</title>")

        for name, content in tags.items():
            if ":" in name:  # For property attributes (og:, twitter:)
                html_tags.append(f'<meta property="{html.escape(name)}" content="{html.escape(content)}" />')
            else:  # For name attributes
                html_tags.append(f'<meta name="{html.escape(name)}" content="{html.escape(content)}" />')

        # Build final HTML
        meta_html = "\\n".join(html_tags)

        result = {"html": meta_html, "tags": tags}
        return {"result": result, "error": None}

    except Exception as e:
        logger.error(f"Error generating meta tags: {e}", exc_info=True)
        return {
            "result": None,
            "error": f"Failed to generate meta tags: {str(e)}",
        }
