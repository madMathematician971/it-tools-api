"""Tool for calculating Estimated Time of Arrival (ETA)."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from mcp_server import mcp_app

logger = logging.getLogger(__name__)


@mcp_app.tool()
def calculate_eta(start_time_iso: str, duration_seconds: int) -> dict[str, Any]:
    """
    Calculates the end datetime by adding a duration (in seconds) to a start datetime.

    Args:
        start_time_iso: The starting datetime in ISO 8601 format (e.g., '2023-10-27T10:00:00Z').
                        Timezone information is required for accurate calculation.
        duration_seconds: The duration in seconds to add (must be non-negative).

    Returns:
        A dictionary containing:
            start_time: The validated start time in ISO 8601 format (UTC if no timezone given).
            duration_seconds: The provided duration in seconds.
            end_time: The calculated end time in ISO 8601 format.
            error: An error message if calculation failed, otherwise None.
    """
    if duration_seconds < 0:
        return {
            "start_time": None,
            "duration_seconds": duration_seconds,
            "end_time": None,
            "error": "Duration must be non-negative.",
        }

    try:
        # Parse the ISO 8601 start time string
        try:
            start_dt = datetime.fromisoformat(start_time_iso)
        except ValueError:
            return {
                "start_time": None,
                "duration_seconds": duration_seconds,
                "end_time": None,
                "error": "Invalid start_time_iso format. Please use ISO 8601 format.",
            }

        # Handle timezone: assume UTC if naive, log warning
        start_time_out_iso = start_time_iso  # Store original for output unless changed
        if start_dt.tzinfo is None or start_dt.tzinfo.utcoffset(start_dt) is None:
            logger.warning(f"Input start_time '{start_time_iso}' lacks timezone info. Assuming UTC.")
            start_dt = start_dt.replace(tzinfo=timezone.utc)
            start_time_out_iso = start_dt.isoformat()  # Update output string to reflect assumed UTC
        else:
            start_time_out_iso = start_dt.isoformat()

        # Calculate the end time
        duration = timedelta(seconds=duration_seconds)
        end_dt = start_dt + duration

        return {
            "start_time": start_time_out_iso,
            "duration_seconds": duration_seconds,
            "end_time": end_dt.isoformat(),
            "error": None,
        }

    except Exception as e:
        logger.error(f"Unexpected error calculating ETA: {e}", exc_info=True)
        return {
            "start_time": None,
            "duration_seconds": duration_seconds,
            "end_time": None,
            "error": f"An unexpected error occurred during ETA calculation: {str(e)}",
        }
