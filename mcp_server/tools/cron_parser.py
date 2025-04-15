"""
Cron expression parsing tools for MCP server.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from cron_descriptor import get_description
from croniter import croniter

from mcp_server import mcp_app

logger = logging.getLogger(__name__)


@mcp_app.tool()
def describe_cron(cron_string: str) -> dict[str, str | None]:
    """
    Get a human-readable description of a cron string (5 or 6 fields).
    Note: Descriptions for 6-field strings might ignore the seconds field.

    Args:
        cron_string: The cron expression to describe (e.g., "*/5 * * * *", "0 * * * * *").

    Returns:
        A dictionary containing:
            description: The human-readable description.
            error: An error message if the string is invalid or description fails.
    """
    try:
        parts = cron_string.split()
        num_parts = len(parts)

        # Explicitly reject <5 or >6 fields
        if num_parts < 5 or num_parts > 6:
            raise ValueError("Cron string must have 5 or 6 fields.")

        # Validate using croniter first (handles basic syntax and ranges)
        if not croniter.is_valid(cron_string):
            try:
                croniter(cron_string)
                raise ValueError("Invalid cron string format.")
            except Exception as ce:
                raise ValueError(f"Invalid cron string format: {ce}") from ce

        # Use cron-descriptor, accepting its potential limitations with 6 fields
        description = get_description(cron_string)
        logger.info(f"Successfully described cron string: {cron_string}")
        return {"description": description, "error": None}

    except ValueError as e:
        error_msg = f"Invalid cron string: {e}"
        logger.warning(error_msg)
        return {"description": None, "error": error_msg}
    except Exception as e:
        # Catch potential errors from get_description itself
        error_msg = f"An unexpected error occurred during cron description: {e}"
        logger.error(error_msg, exc_info=True)
        return {"description": None, "error": error_msg}


@mcp_app.tool()
def validate_cron(cron_string: str) -> dict[str, Any]:
    """
    Validate a cron string and get the next 5 run times.

    Args:
        cron_string: The cron expression to validate (e.g., "0 9 * * MON-FRI").

    Returns:
        A dictionary containing:
            is_valid: Boolean indicating if the cron string is valid.
            next_runs: A list of the next 5 run times in ISO format (UTC), or None if invalid.
            error: An error message if the string is invalid or calculation fails.
    """
    try:
        parts = cron_string.split()
        num_parts = len(parts)

        # Explicitly reject 7+ fields
        if num_parts > 6:
            raise ValueError("Cron string has too many fields (expected 5 or 6).")

        is_valid = croniter.is_valid(cron_string)
        if not is_valid:
            error_msg = "Invalid cron string format."
            logger.warning(f"{error_msg} Input: {cron_string}")
            return {"is_valid": False, "next_runs": None, "error": error_msg}

        # Calculate next 5 runs
        itr = croniter(cron_string)
        next_runs_ts = [itr.get_next(ret_type=float) for _ in range(5)]
        next_runs_iso = [datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() for ts in next_runs_ts]

        logger.info(f"Successfully validated cron string and got next runs: {cron_string}")
        return {"is_valid": True, "next_runs": next_runs_iso, "error": None}

    except ValueError as e:  # Catch potential value errors from croniter instantiation if is_valid somehow passed
        error_msg = f"Error processing cron string: {e}"
        logger.warning(error_msg)
        return {"is_valid": False, "next_runs": None, "error": error_msg}
    except Exception as e:
        error_msg = f"An unexpected error occurred during cron validation: {e}"
        logger.error(error_msg, exc_info=True)
        # Even if an unexpected error occurs, it implies the string wasn't practically valid for getting runs
        return {"is_valid": False, "next_runs": None, "error": error_msg}
