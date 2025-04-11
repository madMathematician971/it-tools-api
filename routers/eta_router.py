import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

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
async def calculate_eta(payload: EtaInput):
    """Calculates the end datetime by adding a duration (in seconds) to a start datetime.

    Both start and end times are returned in ISO 8601 format.
    The input start time should include timezone information.
    """
    try:
        # Parse the ISO 8601 start time string
        try:
            start_dt = datetime.fromisoformat(payload.start_time_iso)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_time_iso format. Please use ISO 8601 format.",
            )

        # Ensure the datetime object is timezone-aware if it wasn't already
        # If no timezone was provided, assume UTC as a sensible default, but log a warning.
        if start_dt.tzinfo is None or start_dt.tzinfo.utcoffset(start_dt) is None:
            logger.warning(f"Input start_time '{payload.start_time_iso}' lacks timezone info. Assuming UTC.")
            start_dt = start_dt.replace(tzinfo=timezone.utc)

        # Calculate the end time
        duration = timedelta(seconds=payload.duration_seconds)
        end_dt = start_dt + duration

        return EtaOutput(
            start_time=start_dt.isoformat(),
            duration_seconds=payload.duration_seconds,
            end_time=end_dt.isoformat(),
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error calculating ETA: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during ETA calculation: {str(e)}",
        )
