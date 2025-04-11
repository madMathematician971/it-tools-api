from fastapi import APIRouter, HTTPException, status

from models.percentage_models import (
    PercentageCalcType,
    PercentageInput,
    PercentageOutput,
)

router = APIRouter(prefix="/api/percentage", tags=["Percentage Calculator"])


@router.post("/calculate", response_model=PercentageOutput)
async def calculate_percentage(payload: PercentageInput):
    """Perform various percentage calculations."""
    v1 = payload.value1
    v2 = payload.value2
    calc_type = payload.calc_type
    description = ""
    result = None

    try:
        if calc_type == PercentageCalcType.percent_of:
            # What is v1% of v2?
            result = (v1 / 100) * v2
            description = f"{v1}% of {v2} is {result}"
        elif calc_type == PercentageCalcType.x_is_what_percent_of_y:
            # v1 is what % of v2?
            if v2 == 0:
                return {
                    "calculation_description": f"{v1} is ?% of {v2}",
                    "error": "Cannot calculate percentage of zero.",
                }
            result = (v1 / v2) * 100
            description = f"{v1} is {result:.2f}% of {v2}"  # Format to 2 decimal places
        elif calc_type == PercentageCalcType.percent_increase:
            # % increase from v1 to v2
            if v1 == 0:
                return {
                    "calculation_description": f"% increase from {v1} to {v2}",
                    "error": "Cannot calculate percentage increase from zero.",
                }
            result = ((v2 - v1) / abs(v1)) * 100  # Use abs(v1) to handle negative start
            description = f"Increase from {v1} to {v2} is {result:.2f}%"
        elif calc_type == PercentageCalcType.percent_decrease:
            # % decrease from v1 to v2
            if v1 == 0:
                return {
                    "calculation_description": f"% decrease from {v1} to {v2}",
                    "error": "Cannot calculate percentage decrease from zero.",
                }
            result = ((v1 - v2) / abs(v1)) * 100  # Use abs(v1)
            description = f"Decrease from {v1} to {v2} is {result:.2f}%"
        else:
            # Should be caught by Pydantic
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid calculation type specified.",
            )

        return {"result": result, "calculation_description": description}

    except Exception as e:
        print(f"Error calculating percentage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during percentage calculation",
        )
