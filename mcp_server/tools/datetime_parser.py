"""
DateTime parsing and formatting tool for MCP server.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from dateutil import parser

from mcp_server import mcp_app

logger = logging.getLogger(__name__)


@mcp_app.tool()
def parse_datetime(
    input_value: str | int | float,
    input_format: str,
    output_format: str,
) -> dict[str, Any]:
    """
    Convert between various date/time formats and timestamps.

    Args:
        input_value: The date/time value (string, int/float for unix timestamp).
        input_format: Format of the input ('unix_s', 'unix_ms', 'iso8601', 'auto').
        output_format: Desired output format ('unix_s', 'unix_ms', 'iso8601',
                       'rfc2822', 'human_readable', 'custom:<pattern>').

    Returns:
        A dictionary containing:
            result: The converted value (string, int, or float).
            parsed_utc_iso: The parsed input as a UTC ISO8601 string.
            error: An error message string if conversion failed, otherwise None.
    """
    dt_object: datetime | None = None
    input_fmt_norm = input_format.lower()
    error_msg: str | None = None

    try:
        # --- Parse Input ---
        if input_fmt_norm == "unix_s":
            if not isinstance(input_value, (int, float)):
                raise ValueError("unix_s input must be a number.")
            dt_object = datetime.fromtimestamp(float(input_value), tz=timezone.utc)
        elif input_fmt_norm == "unix_ms":
            if not isinstance(input_value, (int, float)):
                raise ValueError("unix_ms input must be a number.")
            dt_object = datetime.fromtimestamp(float(input_value) / 1000.0, tz=timezone.utc)
        elif input_fmt_norm == "iso8601":
            if not isinstance(input_value, str):
                raise ValueError("iso8601 input must be a string.")
            dt_object = parser.isoparse(input_value)
            # Assume UTC if no timezone info
            if dt_object.tzinfo is None:
                dt_object = dt_object.replace(tzinfo=timezone.utc)
        elif input_fmt_norm == "auto":
            if isinstance(input_value, (int, float)):
                # Determine if it's likely seconds or milliseconds
                timestamp_val = float(input_value)
                # Heuristic: timestamps around/after 2050 are likely milliseconds
                if timestamp_val > 2524608000:
                    dt_object = datetime.fromtimestamp(timestamp_val / 1000.0, tz=timezone.utc)
                else:
                    dt_object = datetime.fromtimestamp(timestamp_val, tz=timezone.utc)
            elif isinstance(input_value, str):
                # Try parsing as numeric first (unix s/ms)
                try:
                    timestamp_val = float(input_value)
                    if timestamp_val > 2524608000:
                        dt_object = datetime.fromtimestamp(timestamp_val / 1000.0, tz=timezone.utc)
                    else:
                        dt_object = datetime.fromtimestamp(timestamp_val, tz=timezone.utc)
                except ValueError:
                    # If not numeric, try parsing as date string
                    try:
                        dt_object = parser.parse(input_value)
                        if dt_object.tzinfo is None:
                            dt_object = dt_object.replace(tzinfo=timezone.utc)
                    except Exception as parse_err:
                        raise ValueError(
                            f"Could not automatically parse string input: '{input_value}'. Error: {parse_err}"
                        ) from parse_err
            else:
                raise ValueError("'auto' format requires string or numeric input.")
        else:
            raise ValueError(f"Unsupported input_format: '{input_format}'")

        if dt_object is None:
            raise ValueError("Could not parse input value.")

        # Explicitly handle timezone conversion to UTC before timestamping
        if dt_object.tzinfo is not None and dt_object.tzinfo.utcoffset(dt_object) is not None:
            # Convert aware datetime to UTC
            dt_utc = dt_object.astimezone(timezone.utc)
        else:
            # Assume naive datetime is UTC (consistent with earlier logic)
            dt_utc = dt_object.replace(tzinfo=timezone.utc)

        parsed_utc_iso = dt_utc.isoformat(timespec="microseconds").replace("+00:00", "Z")

        # --- Format Output ---
        output_fmt_norm = output_format.lower()
        result_val: str | int | float

        if output_fmt_norm == "unix_s":
            result_val = dt_utc.timestamp()
        elif output_fmt_norm == "unix_ms":
            result_val = dt_utc.timestamp() * 1000.0
        elif output_fmt_norm == "iso8601":
            result_val = parsed_utc_iso
        elif output_fmt_norm == "rfc2822":
            rfc_str = dt_utc.strftime("%a, %d %b %Y %H:%M:%S %z")
            # Replace +0000 with GMT for common RFC2822 representation
            result_val = rfc_str.replace("+0000", "GMT")
        elif output_fmt_norm == "human_readable":
            # Example: Friday, June 28, 2024 at 10:30:45 AM UTC
            result_val = dt_utc.strftime("%A, %B %d, %Y at %I:%M:%S %p") + " UTC"
        elif output_fmt_norm.startswith("custom:"):
            pattern = output_format[len("custom:") :].strip()
            if not pattern:
                raise ValueError("Custom format pattern cannot be empty.")
            try:
                result_val = dt_utc.strftime(pattern)
            except ValueError as strf_err:
                raise ValueError(f"Invalid custom format pattern '{pattern}': {strf_err}") from strf_err
        else:
            raise ValueError(f"Unsupported output_format: '{output_format}'")

        return {"result": result_val, "parsed_utc_iso": parsed_utc_iso, "error": None}

    except ValueError as e:
        error_msg = f"Invalid input or format: {e}"
        logger.warning(error_msg)
        return {"result": None, "parsed_utc_iso": None, "error": error_msg}
    except Exception as e:
        error_msg = f"An unexpected error occurred during date/time conversion: {e}"
        logger.error(error_msg, exc_info=True)
        return {"result": None, "parsed_utc_iso": None, "error": error_msg}
