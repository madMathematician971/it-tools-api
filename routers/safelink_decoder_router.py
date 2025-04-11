import logging
import re
from typing import Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

from fastapi import APIRouter, HTTPException, status

from models.safelink_decoder_models import SafelinkInput, SafelinkOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/safelink-decoder", tags=["Safelink Decoder"])


@router.post("/", response_model=SafelinkOutput)
async def decode_safelink(input_data: SafelinkInput):
    """Decode various types of safe links commonly used by email providers and security tools."""
    try:
        url = input_data.url.strip()
        if not url:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL cannot be empty")

        # Try different decoding methods
        decoders = [
            decode_microsoft_safelink,
            decode_google_safelink,
            decode_proofpoint_safelink,
            decode_generic_redirect,
        ]

        for decoder in decoders:
            decoded_url, method = decoder(url)
            if decoded_url:
                return SafelinkOutput(original_url=url, decoded_url=decoded_url, decoding_method=method)

        # If no decoder worked
        return SafelinkOutput(original_url=input_data.url, error="Unable to decode URL with any known method")

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error decoding safelink: {e}", exc_info=True)
        return SafelinkOutput(original_url=input_data.url, error=f"Error during URL decoding: {str(e)}")


def decode_microsoft_safelink(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Decode Microsoft Office 365 ATP Safe Links."""
    ms_pattern = r"https?://(?:[a-zA-Z0-9][-a-zA-Z0-9]*[a-zA-Z0-9]\.)*safelinks\.protection\.outlook\.com/.*?url="
    if re.match(ms_pattern, url):
        try:
            # Extract the URL parameter
            parsed = urlparse(url)
            params = parse_qs(parsed.query)

            if "url" in params:
                decoded_url = params["url"][0]
                # URL decode the extracted URL
                decoded_url = unquote(decoded_url)
                return decoded_url, "Microsoft Safe Links"
        except Exception as e:
            logger.warning(f"Error decoding Microsoft safelink: {e}")

    return None, None


def decode_google_safelink(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Decode Google Safe Browsing redirects."""
    google_patterns = [r"https?://www\.google\.com/url\?.*?url=", r"https?://security\.google\.com/url\?"]

    for pattern in google_patterns:
        if re.match(pattern, url):
            try:
                parsed = urlparse(url)
                params = parse_qs(parsed.query)

                if "url" in params:
                    decoded_url = params["url"][0]
                    decoded_url = unquote(decoded_url)
                    return decoded_url, "Google Safe Browsing"
                elif "q" in params:
                    potential_url = params["q"][0]
                    unquoted_potential = unquote(potential_url)
                    # Basic check if it looks like a URL after unquoting
                    if re.match(r"^https?://", unquoted_potential):
                        return unquoted_potential, "Google Search Redirect"
                    # If q param doesn't look like a URL, ignore it (could be search term)
            except Exception as e:
                logger.warning(f"Error decoding Google redirect part: {e}", exc_info=True)

    return None, None


def decode_proofpoint_safelink(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Decode Proofpoint URL Defense links."""
    if "urldefense.proofpoint.com" in url:
        try:
            # Proofpoint v1
            if "/v1/" in url:
                parts = url.split("/v1/")
                if len(parts) > 1:
                    encoded_part = parts[1].split("/")[0]
                    decoded_url = unquote(encoded_part)
                    return decoded_url, "Proofpoint URL Defense v1"

            # Proofpoint v2
            if "/v2/" in url:
                params_v2 = parse_qs(urlparse(url).query)
                if "u" in params_v2:
                    # Proper v2 decoding is complex and not implemented here.
                    # Return None, indicating we recognized but couldn't decode.
                    return None, "Proofpoint URL Defense v2 (Decoding not supported)"

            # Newer Proofpoint formats
            parsed = urlparse(url)
            params = parse_qs(parsed.query)

            # Try to find URL parameter with different names
            for param in ["url", "u", "r"]:
                if param in params:
                    decoded_url = params[param][0]
                    decoded_url = unquote(decoded_url)
                    return decoded_url, "Proofpoint URL Defense"
        except Exception as e:
            logger.warning(f"Error decoding Proofpoint safelink: {e}")

    return None, None


def decode_generic_redirect(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Try to decode generic URL redirects with common parameter names."""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        # Common redirect parameter names
        for param in [
            "url",
            "link",
            "target",
            "dest",
            "destination",
            "redirect",
            "redirectUrl",
            "redirect_uri",
            "u",
            "r",
        ]:
            if param in params:
                decoded_url = params[param][0]
                decoded_url = unquote(decoded_url)
                return decoded_url, f"Generic Redirect (param: {param})"
    except Exception as e:
        logger.warning(f"Error decoding generic redirect: {e}")

    return None, None
