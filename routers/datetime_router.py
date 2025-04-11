from datetime import datetime, timezone
from typing import Optional, Union

from dateutil import parser
from fastapi import APIRouter, HTTPException, status

from models.datetime_models import DateTimeConvertInput, DateTimeConvertOutput

router = APIRouter(prefix="/api/datetime", tags=["DateTime"])


@router.post("/convert", response_model=DateTimeConvertOutput)
async def datetime_convert(payload: DateTimeConvertInput):
    """Convert between various date/time formats and timestamps."""
    dt_object: Optional[datetime] = None
    input_fmt = payload.input_format.lower()
    input_val = payload.input_value

    try:
        # --- Parse Input ---
        if input_fmt == "unix_s":
            if not isinstance(input_val, (int, float)):
                raise ValueError("unix_s input must be a number.")
            dt_object = datetime.fromtimestamp(float(input_val), tz=timezone.utc)
        elif input_fmt == "unix_ms":
            if not isinstance(input_val, (int, float)):
                raise ValueError("unix_ms input must be a number.")
            dt_object = datetime.fromtimestamp(float(input_val) / 1000.0, tz=timezone.utc)
        elif input_fmt == "iso8601":
            if not isinstance(input_val, str):
                raise ValueError("iso8601 input must be a string.")
            dt_object = parser.isoparse(input_val)
            if dt_object.tzinfo is None:
                dt_object = dt_object.replace(tzinfo=timezone.utc)
        elif input_fmt == "auto":
            if isinstance(input_val, (int, float)):
                timestamp_val = float(input_val)
                if timestamp_val > 2524608000:
                    dt_object = datetime.fromtimestamp(timestamp_val / 1000.0, tz=timezone.utc)
                else:
                    dt_object = datetime.fromtimestamp(timestamp_val, tz=timezone.utc)
            elif isinstance(input_val, str):
                try:
                    timestamp_val = float(input_val)
                    if timestamp_val > 2524608000:
                        dt_object = datetime.fromtimestamp(timestamp_val / 1000.0, tz=timezone.utc)
                    else:
                        dt_object = datetime.fromtimestamp(timestamp_val, tz=timezone.utc)
                except ValueError:
                    try:
                        dt_object = parser.parse(input_val)
                        if dt_object.tzinfo is None:
                            dt_object = dt_object.replace(tzinfo=timezone.utc)
                    except Exception as parse_err:
                        raise ValueError(f"Could not automatically parse string input: {parse_err}")
            else:
                raise ValueError("'auto' format requires string or numeric input.")
        else:
            raise ValueError(f"Unsupported input_format: {payload.input_format}")

        if dt_object is None:
            raise ValueError("Could not parse input value.")

        dt_utc = dt_object.astimezone(timezone.utc)
        parsed_utc_iso = dt_utc.isoformat(timespec="microseconds").replace("+00:00", "Z")

        # --- Format Output ---
        output_fmt = payload.output_format.lower()
        result: Union[str, int, float]

        if output_fmt == "unix_s":
            result = dt_utc.timestamp()
        elif output_fmt == "unix_ms":
            result = dt_utc.timestamp() * 1000.0
        elif output_fmt == "iso8601":
            result = parsed_utc_iso
        elif output_fmt == "rfc2822":
            rfc_str = dt_utc.strftime("%a, %d %b %Y %H:%M:%S %z")
            result = rfc_str.replace("+0000", "GMT")
        elif output_fmt == "human_readable":
            result = dt_utc.strftime("%A, %B %d, %Y at %I:%M:%S %p") + " UTC"
        elif output_fmt.startswith("custom:"):
            pattern = payload.output_format[len("custom:") :]
            try:
                result = dt_utc.strftime(pattern)
            except ValueError as strf_err:
                raise ValueError(f"Invalid custom format pattern '{pattern}': {strf_err}")
        else:
            raise ValueError(f"Unsupported output_format: {payload.output_format}")

        return {
            "result": result,
            "input_value": payload.input_value,
            "input_format": payload.input_format,
            "output_format": payload.output_format,
            "parsed_utc_iso": parsed_utc_iso,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input or format: {e}",
        )
    except Exception as e:
        print(f"Error converting date/time: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during date/time conversion",
        )
