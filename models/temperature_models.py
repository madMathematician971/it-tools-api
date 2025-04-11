from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TemperatureUnit(str, Enum):
    celsius = "celsius"
    fahrenheit = "fahrenheit"
    kelvin = "kelvin"


class TemperatureInput(BaseModel):
    value: float
    unit: TemperatureUnit = Field(..., description="Unit of the input value")


class TemperatureOutput(BaseModel):
    celsius: float
    fahrenheit: float
    kelvin: float
    error: Optional[str] = None
