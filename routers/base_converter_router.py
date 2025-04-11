import string

from fastapi import APIRouter, HTTPException, status

from models.base_converter_models import BaseConvertInput, BaseConvertOutput

router = APIRouter(prefix="/api/base", tags=["Base Converter"])


# Helper function to convert integer to arbitrary base (2-36)
def int_to_base(n: int, base: int) -> str:
    if n == 0:
        return "0"
    if base < 2 or base > 36:
        raise ValueError("Base must be between 2 and 36")

    digits = string.digits + string.ascii_lowercase
    result = ""
    is_negative = n < 0
    n = abs(n)

    while n > 0:
        result = digits[n % base] + result
        n //= base

    return ("-" if is_negative else "") + result


@router.post("/convert", response_model=BaseConvertOutput)
async def base_convert(payload: BaseConvertInput):
    """Convert an integer between different bases (2-36)."""
    try:
        # Convert input string in input_base to integer (base 10)
        input_number_int = int(payload.number_string, payload.input_base)

        # Convert integer (base 10) to output_base string
        result_str = int_to_base(input_number_int, payload.output_base)

        return {
            "result_string": result_str,
            "input_number_string": payload.number_string,
            "input_base": payload.input_base,
            "output_base": payload.output_base,
        }
    except ValueError as e:
        # Handles invalid digits for input_base or invalid bases
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid input: {e}")
    except Exception as e:
        print(f"Error converting base: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during base conversion",
        )
