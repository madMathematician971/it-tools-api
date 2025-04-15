import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query, status

from mcp_server.tools.uuid_generator import generate_uuid as generate_uuid_tool
from models.uuid_models import UuidInput, UuidOutput, UuidResponse

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/uuid", tags=["UUID Generator"])


@router.get("/", response_model=UuidResponse)
async def get_uuid_details_endpoint(
    version: int = Query(4, description="UUID version to generate (1 or 4)", ge=1, le=4)
):
    """Generate a UUID of the specified version (1 or 4) with detailed info."""
    # Restore explicit check for supported versions for this specific GET endpoint
    if version not in [1, 4]:
        # Although Query parameter restricts this, add explicit check for clarity and robustness
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported UUID version for this endpoint: {version}. Only versions 1 and 4 are supported via GET.",
        )

    try:
        # Call the tool function (now guaranteed to be v1 or v4)
        result_dict = generate_uuid_tool(version=version)

        # Check for errors (should be very unlikely now)
        if result_dict.get("error"):
            logger.warning(f"UUID generation (v{version}) unexpectedly failed: {result_dict['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result_dict["error"],
            )

        # Tool's result dictionary directly matches UuidResponse model
        return result_dict

    except ValueError as e:
        # Catch potential errors from tool (e.g., if version somehow bypasses Query validation)
        logger.info(f"Invalid version for GET /uuid: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:  # Re-raise
        raise
    except Exception as e:
        logger.error(f"Error getting UUID details (v{version}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error generating UUID details"
        )


@router.post("/v{version}", response_model=UuidOutput)
async def generate_uuid_post_endpoint(version: int = Path(..., ge=1, le=5), payload: Optional[UuidInput] = None):
    """Generate a UUID of the specified version (1, 3, 4, or 5)."""
    try:
        # Prepare args for the tool
        namespace_arg = payload.namespace if payload else None
        name_arg = payload.name if payload else None

        # Call the tool function
        result_dict = generate_uuid_tool(version=version, namespace=namespace_arg, name=name_arg)

        # Check for errors from the tool
        if result_dict.get("error"):
            logger.info(f"UUID generation (v{version}) failed: {result_dict['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result_dict["error"],
            )

        # Extract required fields for the simpler UuidOutput model
        return UuidOutput(version=result_dict["version"], uuid=result_dict["uuid"])

    except ValueError as e:
        # Catch errors from tool (invalid version, missing ns/name, invalid ns format)
        logger.warning(f"Invalid input for UUID generation (v{version}): {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:  # Re-raise
        raise
    except Exception as e:
        logger.error(f"Error generating UUID (v{version}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error generating UUID"
        )
