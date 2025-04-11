from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PercentageCalcType(str, Enum):
    percent_of = "percent_of"  # What is X% of Y?
    x_is_what_percent_of_y = "x_is_what_percent_of_y"  # X is what % of Y?
    percent_increase = "percent_increase"  # % increase from X to Y
    percent_decrease = "percent_decrease"  # % decrease from X to Y


class PercentageInput(BaseModel):
    value1: float = Field(..., description="First value (X)")
    value2: float = Field(..., description="Second value (Y)")
    calc_type: PercentageCalcType = Field(..., description="Type of calculation to perform")


class PercentageOutput(BaseModel):
    result: Optional[float] = None
    calculation_description: str
    error: Optional[str] = None
