import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.cron_parser import describe_cron, validate_cron
from models.cron_models import CronDescribeOutput, CronInput, CronValidateOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cron", tags=["Cron"])


@router.post("/describe", response_model=CronDescribeOutput)
async def cron_describe_endpoint(payload: CronInput):
    """Get a human-readable description of a cron string using the tool."""
    try:
        result = describe_cron(cron_string=payload.cron_string)

        if result["error"]:
            tool_error_msg = result["error"]
            if "Invalid cron string" in tool_error_msg:
                logger.warning(
                    f"Invalid cron string for description: {payload.cron_string} - Tool Error: {tool_error_msg}"
                )
                # Pass the specific error from the tool
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=tool_error_msg)
            # Log other tool errors and return a generic 500
            logger.error(f"Cron describe tool returned an unexpected error: {tool_error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during description",
            )

        # Tool executed successfully
        return CronDescribeOutput(description=result["description"])

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error in /cron/describe endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during description",
        )


@router.post("/validate", response_model=CronValidateOutput)
async def cron_validate_endpoint(payload: CronInput):
    """Validate a cron string and get the next few run times using the tool."""
    try:
        result = validate_cron(cron_string=payload.cron_string)

        # The tool returns is_valid, next_runs, and error directly
        # If there's an error (even unexpected), the tool returns is_valid=False
        if not result["is_valid"]:
            # Log the error if present, but return structure based on is_valid
            if result["error"]:
                logger.warning(f"Cron validation failed for '{payload.cron_string}': {result['error']}")
            return CronValidateOutput(is_valid=False, error=result.get("error"))  # Pass error if available

        # Tool executed successfully and string is valid
        return CronValidateOutput(is_valid=True, next_runs=result["next_runs"])

    except Exception as e:
        # Catch unexpected errors *calling* the tool (should be rare)
        logger.error(f"Unexpected error calling /cron/validate tool: {e}", exc_info=True)
        # Mimic the tool's error response structure for consistency
        return CronValidateOutput(is_valid=False, error="Unexpected internal server error during validation.")
