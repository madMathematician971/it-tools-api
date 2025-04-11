import logging
from urllib.parse import parse_qs, urlparse

from fastapi import APIRouter, HTTPException, status

from models.url_parser_models import UrlParserInput, UrlParserOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/url-parser", tags=["URL Parser"])


@router.post("/", response_model=UrlParserOutput)
async def parse_url(input_data: UrlParserInput):
    """Parse a URL into its components."""
    url = input_data.url.strip()
    if not url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL cannot be empty")

    # Parse URL
    parsed = urlparse(url)

    # Parse query parameters if present
    query_params = {}
    if parsed.query:
        query_params = parse_qs(parsed.query)

    # Build result
    return UrlParserOutput(
        original_url=url,
        scheme=parsed.scheme,
        netloc=parsed.netloc,
        path=parsed.path,
        params=parsed.params,
        query=parsed.query,
        fragment=parsed.fragment,
        username=parsed.username,
        password=parsed.password,
        hostname=parsed.hostname,
        port=parsed.port,
        query_params=query_params,
    )
