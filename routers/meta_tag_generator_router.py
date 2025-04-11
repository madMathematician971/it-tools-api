import html
import logging

from fastapi import APIRouter, HTTPException, status

from models.meta_tag_generator_models import MetaTagInput, MetaTagOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meta-tag-generator", tags=["Meta Tag Generator"])


@router.post("/", response_model=MetaTagOutput)
async def generate_meta_tags(input_data: MetaTagInput):
    """Generate HTML meta tags based on provided input data."""
    try:
        # Initialize dictionary to store tags
        tags = {}

        # Generate basic meta tags
        tags["title"] = input_data.title
        tags["description"] = input_data.description

        if input_data.keywords:
            tags["keywords"] = input_data.keywords

        if input_data.author:
            tags["author"] = input_data.author

        tags["language"] = input_data.language
        tags["robots"] = input_data.robots
        tags["viewport"] = input_data.viewport

        # Generate Open Graph tags
        tags["og:title"] = input_data.title
        tags["og:description"] = input_data.description
        tags["og:type"] = input_data.og_type

        if input_data.og_url:
            tags["og:url"] = input_data.og_url

        if input_data.og_image:
            tags["og:image"] = input_data.og_image

        # Generate Twitter Card tags
        tags["twitter:title"] = input_data.title
        tags["twitter:description"] = input_data.description
        tags["twitter:card"] = input_data.twitter_card

        if input_data.twitter_site:
            tags["twitter:site"] = input_data.twitter_site

        # Generate HTML
        html_tags = []
        html_tags.append(f"<title>{html.escape(input_data.title)}</title>")

        for name, content in tags.items():
            if ":" in name:  # For property attributes (og:, twitter:)
                html_tags.append(f'<meta property="{html.escape(name)}" content="{html.escape(content)}" />')
            else:  # For name attributes
                html_tags.append(f'<meta name="{html.escape(name)}" content="{html.escape(content)}" />')

        # Build final HTML
        meta_html = "\n".join(html_tags)

        return MetaTagOutput(html=meta_html, tags=tags)

    except Exception as e:
        logger.error(f"Error generating meta tags: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate meta tags: {str(e)}"
        )
