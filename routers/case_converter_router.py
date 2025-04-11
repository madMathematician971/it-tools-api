import caseconverter
from fastapi import APIRouter, HTTPException, status

from models.case_converter_models import CaseConvertInput, CaseConvertOutput

router = APIRouter(prefix="/api/case", tags=["Case Converter"])


@router.post("/convert", response_model=CaseConvertOutput)
async def case_convert(payload: CaseConvertInput):
    """Convert string to a specified case."""
    try:
        # Use functions directly from caseconverter (without underscores)
        supported_cases = {
            "camel": caseconverter.camelcase,
            "snake": caseconverter.snakecase,
            "pascal": caseconverter.pascalcase,
            "constant": caseconverter.macrocase,  # constant_case -> macrocase
            "kebab": caseconverter.kebabcase,
            "capital": caseconverter.titlecase,
            # Removed unsupported cases for v1.2.0
            # "dot": caseconverter.dotcase,
            # "header": caseconverter.headercase,
            # "sentence": caseconverter.sentencecase,
            # "path": caseconverter.pathcase,
            "lower": lambda s: s.lower(),
            "upper": lambda s: s.upper(),
        }
        target = payload.target_case.lower().replace("-", "_")

        if target not in supported_cases:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid target_case. Supported cases: {list(supported_cases.keys())}",
            )

        # Check if the function exists before calling
        conversion_func = supported_cases.get(target)
        if not conversion_func:
            # This case should theoretically be caught by the check above, but added for safety
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Case conversion function for '{target}' not found.",
            )

        result = conversion_func(payload.input)
        return {"result": result}
    except AttributeError as e:
        # Handle cases where a specific function might be missing in the library version
        print(f"Missing case function in caseconverter: {e}")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Case '{payload.target_case}' is not supported by the current library version.",
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error converting case: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during case conversion",
        )
