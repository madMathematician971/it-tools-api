import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.case_converter import convert_case
from models.case_converter_models import CaseConvertInput, CaseConvertOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/case", tags=["Case Converter"])


@router.post("/convert", response_model=CaseConvertOutput)
async def case_convert_endpoint(payload: CaseConvertInput):
    """Convert string to a specified case using the tool."""
    try:
        result = convert_case(input_string=payload.input, target_case=payload.target_case)

        if result["error"]:
            # Check for specific user errors from the tool
            if "Invalid target_case" in result["error"]:
                logger.warning(f"Invalid target case provided: {payload.target_case}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result["error"],
                )
            if "not supported by the installed caseconverter" in result["error"]:
                # Handle case where library version might be incompatible (AttributeError in tool)
                logger.error(f"Case converter tool reported library incompatibility: {result['error']}")
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail=f"Case '{payload.target_case}' is not supported by the current library version.",
                )
            # Log other tool errors and return a generic 500
            logger.error(f"Case converter tool returned an unexpected error: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during case conversion",
            )

        # Tool executed successfully
        return CaseConvertOutput(result=result["result"])

    except HTTPException as http_exc:  # Re-raise HTTPException for specific error handling above
        raise http_exc
    except Exception as e:
        # Catch any unexpected exceptions during the tool call or processing
        logger.error(f"Unexpected error in /case/convert endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during case conversion",
        )
