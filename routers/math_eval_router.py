import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.math_evaluator import evaluate_math as evaluate_math_tool
from models.math_eval_models import MathEvalInput, MathEvalOutput

router = APIRouter(prefix="/api/math", tags=["Math"])
logger = logging.getLogger(__name__)


@router.post("/evaluate", response_model=MathEvalOutput)
async def evaluate_math_expression_endpoint(payload: MathEvalInput):
    """Safely evaluate a mathematical expression string."""
    try:
        # Call the tool function
        result_dict = evaluate_math_tool(expression=payload.expression)

        # Check for errors returned by the tool
        if result_dict.get("error"):
            logger.info(f"Math evaluation failed: {result_dict['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result_dict["error"],
            )

        return result_dict

    # Keep general exception handler for unexpected errors
    except HTTPException:  # Re-raise
        raise
    except Exception as e:
        logger.error(f"Error evaluating math expression: {e}", exc_info=True)
        # Return error structure expected by the response model for 500 errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during evaluation: {str(e)}",
        )
