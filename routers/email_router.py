import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.email_processor import normalize_email
from models.email_models import EmailInput, EmailNormalizeOutput

router = APIRouter(prefix="/api/email", tags=["Email"])

logger = logging.getLogger(__name__)


@router.post("/normalize", response_model=EmailNormalizeOutput)
async def email_normalize_endpoint(payload: EmailInput):
    """Normalize an email address using the MCP tool."""
    email_address = payload.email

    try:
        # Call the tool function
        result = normalize_email(email_address=email_address)

        # Check for errors from the tool
        if error := result.get("error"):
            logger.warning(f"Email normalization tool failed for '{email_address}': {error}")
            # Most tool errors indicate bad input
            if "Internal server error" in error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Tool error: {error}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid input: {error}")

        # Get normalized email
        normalized_email = result.get("normalized_email")
        if normalized_email is None:
            # Should not happen if error is None
            logger.error("Tool returned no error but also no normalized email.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal error: Tool failed to produce normalized email.",
            )

        # Return the original and normalized email
        return {
            "normalized_email": normalized_email,
            "original_email": result.get("original_email"),  # Use original from tool result
        }

    except HTTPException as e:
        # Re-raise HTTP exceptions directly
        raise e
    except Exception as e:
        # Catch unexpected errors
        logger.error(f"Unexpected error normalizing email: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )
