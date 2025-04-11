import logging

from fastapi import APIRouter, HTTPException, status
from user_agents import parse

from models.user_agent_parser_models import UserAgentInput, UserAgentOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user-agent-parser", tags=["User Agent Parser"])


@router.post("/", response_model=UserAgentOutput)
async def parse_user_agent(input_data: UserAgentInput):
    """Parse a User-Agent string to extract browser, OS, and device information."""
    try:
        user_agent_string = input_data.user_agent.strip()
        if not user_agent_string:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User-Agent string cannot be empty")

        # Parse the user agent
        parsed_ua = parse(user_agent_string)

        # Extract browser info with defaults for missing values
        browser = {
            "family": parsed_ua.browser.family or "Unknown",
            "version": parsed_ua.browser.version_string or "",
            "version_major": str(parsed_ua.browser.version[0]) if parsed_ua.browser.version else "",
            "version_minor": (
                str(parsed_ua.browser.version[1])
                if parsed_ua.browser.version and len(parsed_ua.browser.version) > 1
                else ""
            ),
            "version_patch": (
                str(parsed_ua.browser.version[2])
                if parsed_ua.browser.version and len(parsed_ua.browser.version) > 2
                else ""
            ),
        }

        # Extract OS info with defaults for missing values
        os = {
            "family": parsed_ua.os.family or "Unknown",
            "version": parsed_ua.os.version_string or "",
            "version_major": str(parsed_ua.os.version[0]) if parsed_ua.os.version else "",
            "version_minor": (
                str(parsed_ua.os.version[1]) if parsed_ua.os.version and len(parsed_ua.os.version) > 1 else ""
            ),
            "version_patch": (
                str(parsed_ua.os.version[2]) if parsed_ua.os.version and len(parsed_ua.os.version) > 2 else ""
            ),
        }

        # Extract device info with defaults and correct boolean types
        device = {
            "family": parsed_ua.device.family or "Unknown",
            "brand": parsed_ua.device.brand or "",
            "model": parsed_ua.device.model or "",
            "is_mobile": parsed_ua.is_mobile,
            "is_tablet": parsed_ua.is_tablet,
            "is_pc": parsed_ua.is_pc,
            "is_bot": parsed_ua.is_bot,
            "is_touch_capable": parsed_ua.is_touch_capable,
        }

        return UserAgentOutput(browser=browser, os=os, device=device, raw_user_agent=user_agent_string)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error parsing user agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to parse User-Agent: {str(e)}"
        )
