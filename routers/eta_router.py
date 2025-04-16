import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Import the tool function
from mcp_server.tools.eta_calculator import calculate_eta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/eta", tags=["ETA Calculator"])


class EtaInput(BaseModel):
    start_time_iso: str = Field(
        ...,
        description="The starting datetime in ISO 8601 format (e.g., '2023-10-27T10:00:00Z' or '2023-10-27T12:00:00+02:00').",
    )
    duration_seconds: int = Field(..., description="The duration in seconds to add to the start time.", ge=0)


class EtaOutput(BaseModel):
    start_time: str = Field(..., description="The provided start time in ISO 8601 format.")
    duration_seconds: int = Field(..., description="The provided duration in seconds.")
    end_time: str = Field(..., description="The calculated end time in ISO 8601 format.")


@router.post(
    "/calculate",
    response_model=EtaOutput,
    summary="Calculate end time from start time and duration",
)
async def calculate_eta_endpoint(payload: EtaInput):
    """Calculates the end datetime by adding a duration (in seconds) to a start datetime using the MCP tool.

    Both start and end times are returned in ISO 8601 format.
    """
    try:
        result = calculate_eta(start_time_iso=payload.start_time_iso, duration_seconds=payload.duration_seconds)

        if error := result.get("error"):
            logger.warning(f"ETA calculation tool failed: {error}")
            if "Invalid start_time_iso format" in error or "Duration must be non-negative" in error:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid input: {error}")
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Tool error: {error}")

        # Extract results from the tool output
        start_time = result.get("start_time")
        end_time = result.get("end_time")
        duration = result.get("duration_seconds")

        # Basic check to ensure tool returned expected fields on success
        if start_time is None or end_time is None or duration is None:
            logger.error("Tool succeeded but returned incomplete data.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal error: Tool failed to provide complete results.",
            )

        return EtaOutput(
            start_time=start_time,
            duration_seconds=duration,
            end_time=end_time,
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error calculating ETA: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during ETA calculation: {str(e)}",
        )
