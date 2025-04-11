from typing import Optional, Union

from pydantic import BaseModel, Field


class MathEvalInput(BaseModel):
    expression: str = Field(..., description="Mathematical expression to evaluate")


class MathEvalOutput(BaseModel):
    result: Optional[Union[int, float, bool]] = None  # Result can be number or boolean
    error: Optional[str] = None
