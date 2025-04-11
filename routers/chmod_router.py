from fastapi import APIRouter, HTTPException, status

from models.chmod_models import ChmodNumericInput, ChmodNumericOutput, ChmodSymbolicInput, ChmodSymbolicOutput

router = APIRouter(prefix="/api/chmod", tags=["chmod"])


@router.post("/calculate-numeric", response_model=ChmodNumericOutput)
async def chmod_calculate_numeric(payload: ChmodNumericInput):
    """Calculate the numeric chmod value from owner/group/other permissions."""
    try:
        owner_val = (
            (4 if payload.owner.read else 0) | (2 if payload.owner.write else 0) | (1 if payload.owner.execute else 0)
        )
        group_val = (
            (4 if payload.group.read else 0) | (2 if payload.group.write else 0) | (1 if payload.group.execute else 0)
        )
        others_val = (
            (4 if payload.others.read else 0)
            | (2 if payload.others.write else 0)
            | (1 if payload.others.execute else 0)
        )
        numeric_str = f"{owner_val}{group_val}{others_val}"
        return {"numeric": numeric_str}
    except Exception as e:
        print(f"Error calculating numeric chmod: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during numeric calculation",
        )


@router.post("/calculate-symbolic", response_model=ChmodSymbolicOutput)
async def chmod_calculate_symbolic(payload: ChmodSymbolicInput):
    """Convert a numeric chmod value (e.g., 755, "755") to symbolic representation."""
    try:
        numeric_str = str(payload.numeric).strip()
        if len(numeric_str) == 4 and numeric_str.startswith("0"):  # Allow optional leading 0
            numeric_str = numeric_str[1:]

        # Pad single digit 0-7 to three digits
        if len(numeric_str) == 1 and numeric_str.isdigit() and 0 <= int(numeric_str) <= 7:
            numeric_str = numeric_str.zfill(3)

        if not numeric_str.isdigit() or len(numeric_str) != 3:
            raise ValueError("Numeric value must be 3 digits (e.g., 755 or 0755) or a single valid digit (0-7).")

        owner_val = int(numeric_str[0])
        group_val = int(numeric_str[1])
        others_val = int(numeric_str[2])

        if not (0 <= owner_val <= 7 and 0 <= group_val <= 7 and 0 <= others_val <= 7):
            raise ValueError("Each digit must be between 0 and 7.")

        def get_symbol(val):
            r = "r" if (val & 4) else "-"
            w = "w" if (val & 2) else "-"
            x = "x" if (val & 1) else "-"
            return f"{r}{w}{x}"

        symbolic_str = f"{get_symbol(owner_val)}{get_symbol(group_val)}{get_symbol(others_val)}"
        return {"symbolic": symbolic_str}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid numeric input: {e}",
        )
    except Exception as e:
        print(f"Error calculating symbolic chmod: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during symbolic calculation",
        )
