import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.chmod_calculator import calculate_numeric_chmod, calculate_symbolic_chmod
from models.chmod_models import ChmodNumericInput, ChmodNumericOutput, ChmodSymbolicInput, ChmodSymbolicOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chmod", tags=["chmod"])


@router.post("/calculate-numeric", response_model=ChmodNumericOutput)
async def chmod_calculate_numeric_endpoint(payload: ChmodNumericInput):
    """Calculate the numeric chmod value from symbolic permissions using the tool."""
    try:
        result = calculate_numeric_chmod(
            owner_read=payload.owner.read,
            owner_write=payload.owner.write,
            owner_execute=payload.owner.execute,
            group_read=payload.group.read,
            group_write=payload.group.write,
            group_execute=payload.group.execute,
            others_read=payload.others.read,
            others_write=payload.others.write,
            others_execute=payload.others.execute,
        )

        if result["error"]:
            # Log tool errors and return a generic 500
            logger.error(f"Chmod numeric tool returned an error: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during numeric calculation",
            )

        # Tool executed successfully
        return ChmodNumericOutput(numeric=result["numeric_chmod"])

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error in /chmod/calculate-numeric endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected internal server error",
        )


@router.post("/calculate-symbolic", response_model=ChmodSymbolicOutput)
async def chmod_calculate_symbolic_endpoint(payload: ChmodSymbolicInput):
    """Convert a numeric chmod value to symbolic representation using the tool."""
    try:
        result = calculate_symbolic_chmod(numeric_chmod_string=str(payload.numeric))

        if result["error"]:
            tool_error_msg = result["error"]
            # Check for specific user errors from the tool and map them to original API errors
            if "Numeric value must resolve to 3 digits" in tool_error_msg:
                logger.warning(
                    f"Invalid numeric chmod input (format/length): {payload.numeric} - Tool Error: {tool_error_msg}"
                )
                # Raise HTTPException with the ORIGINAL expected error message
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid numeric input: Numeric value must be 3 digits (e.g., 755 or 0755) or a single valid digit (0-7).",
                )
            if "Each digit must be between 0 and 7" in tool_error_msg:
                logger.warning(
                    f"Invalid numeric chmod input (digit range): {payload.numeric} - Tool Error: {tool_error_msg}"
                )
                # Raise HTTPException with the ORIGINAL expected error message (which matches tool error here)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=tool_error_msg,  # Original message matches tool message
                )
            # Log other tool errors and return a generic 500
            logger.error(f"Chmod symbolic tool returned an unexpected error: {tool_error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during symbolic calculation",
            )

        # Tool executed successfully
        return ChmodSymbolicOutput(symbolic=result["symbolic_chmod"])

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error in /chmod/calculate-symbolic endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during symbolic calculation",
        )
