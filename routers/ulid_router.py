import datetime
import logging

from fastapi import APIRouter, HTTPException, Query, status
from ulid import from_timestamp, new

from models.ulid_models import UlidResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ulid", tags=["ULID Generator"])


@router.get("/", response_model=UlidResponse)
async def generate_ulid(
    timestamp: float = Query(
        None, description="Optional timestamp (Unix epoch seconds) to use. If None, current time is used."
    )
):
    """Generate a Universally Unique Lexicographically Sortable Identifier (ULID)."""
    try:
        if timestamp is not None:
            # Create ULID from timestamp
            # Convert seconds to datetime object
            dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
            ulid = from_timestamp(dt)
        else:
            # Generate a new ULID with current time
            ulid = new()

        # Extract timestamp information
        ts_ms = ulid.timestamp().int
        ts_dt = datetime.datetime.fromtimestamp(ts_ms / 1000, tz=datetime.timezone.utc)
        ts_iso = ts_dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

        # Extract randomness part using bytes slicing and call hex()
        randomness = ulid.bytes[6:].hex()

        return UlidResponse(
            ulid=str(ulid),
            timestamp=ts_iso,
            timestamp_ms=ts_ms,
            randomness=randomness,
        )

    except Exception as e:
        logger.error(f"Error generating ULID: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate ULID: {str(e)}",
        )
