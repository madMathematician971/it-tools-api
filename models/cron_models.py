from typing import List, Optional

from pydantic import BaseModel, Field


class CronInput(BaseModel):
    cron_string: str = Field(..., description="Cron string to parse/validate (e.g., '*/5 * * * *')")


class CronDescribeOutput(BaseModel):
    description: str


class CronValidateOutput(BaseModel):
    is_valid: bool
    next_runs: Optional[List[str]] = None  # Example: first 5 runs
    error: Optional[str] = None
