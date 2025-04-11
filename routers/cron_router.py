from datetime import datetime, timezone

from cron_descriptor import get_description
from croniter import croniter
from fastapi import APIRouter, HTTPException, status

from models.cron_models import CronDescribeOutput, CronInput, CronValidateOutput

router = APIRouter(prefix="/api/cron", tags=["Cron"])


@router.post("/describe", response_model=CronDescribeOutput)
async def cron_describe(payload: CronInput):
    """Get a human-readable description of a cron string."""
    try:
        if not croniter.is_valid(payload.cron_string):
            raise ValueError("Invalid cron string format.")
        description = get_description(payload.cron_string)
        return {"description": description}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid cron string: {e}")
    except Exception as e:
        print(f"Error describing cron string: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during description",
        )


@router.post("/validate", response_model=CronValidateOutput)
async def cron_validate(payload: CronInput):
    """Validate a cron string and get the next few run times."""
    try:
        is_valid = croniter.is_valid(payload.cron_string)
        if not is_valid:
            return {"is_valid": False, "error": "Invalid cron string format."}

        itr = croniter(payload.cron_string)
        next_runs = [itr.get_next(ret_type=float) for _ in range(5)]
        next_runs_iso = [datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() for ts in next_runs]

        return {"is_valid": True, "next_runs": next_runs_iso}
    except Exception as e:
        print(f"Error validating cron string: {e}")
        return {"is_valid": False, "error": "Error during validation processing."}
