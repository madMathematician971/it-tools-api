import logging  # Import logging

from fastapi import APIRouter, HTTPException, status

# Import tool function
from mcp_server.tools.jwt_processor import parse_jwt as parse_jwt_tool
from models.jwt_models import JwtInput, JwtOutput

router = APIRouter(prefix="/api/jwt", tags=["JWT"])
logger = logging.getLogger(__name__)  # Set up logger


@router.post("/parse", response_model=JwtOutput)
async def parse_jwt_endpoint(payload: JwtInput):
    """Decode a JWT and optionally verify its signature."""
    try:
        # Call the tool function
        result_dict = parse_jwt_tool(
            jwt_string=payload.jwt_string,
            secret_or_key=payload.secret_or_key,
            algorithms=payload.algorithms,
        )

        # Check for errors returned by the tool
        # Specific parsing/verification errors are handled by the tool
        # The router mainly handles the 400 response based on tool's error field
        if result_dict.get("error"):
            logger.info(f"JWT parsing/verification failed: {result_dict['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result_dict["error"],
            )

        # Return the successful result from the tool
        # The tool's return dict matches the JwtOutput model structure
        return result_dict

    except HTTPException:  # Re-raise HTTPExceptions (e.g., 400 Bad Request)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in JWT endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during JWT processing: {str(e)}",
        )
