import math  # Import math functions for simpleeval

from fastapi import APIRouter
from simpleeval import FunctionNotDefined, InvalidExpression, NameNotDefined, simple_eval

from models.math_eval_models import MathEvalInput, MathEvalOutput

router = APIRouter(prefix="/api/math", tags=["Math"])

# Define safe functions allowed in simpleeval
SAFE_FUNCTIONS = {
    "abs": abs,
    "acos": math.acos,
    "asin": math.asin,
    "atan": math.atan,
    "atan2": math.atan2,
    "ceil": math.ceil,
    "cos": math.cos,
    "cosh": math.cosh,
    "degrees": math.degrees,
    "exp": math.exp,
    "fabs": math.fabs,
    "floor": math.floor,
    "fmod": math.fmod,
    "frexp": math.frexp,
    "hypot": math.hypot,
    "ldexp": math.ldexp,
    "log": math.log,
    "log10": math.log10,
    "modf": math.modf,
    "pow": math.pow,
    "radians": math.radians,
    "sin": math.sin,
    "sinh": math.sinh,
    "sqrt": math.sqrt,
    "tan": math.tan,
    "tanh": math.tanh,
    # Add other safe functions if needed
}

# Define safe names (constants)
SAFE_NAMES = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
    "true": True,  # Allow boolean literals
    "false": False,
    "none": None,
}


@router.post("/evaluate", response_model=MathEvalOutput)
async def evaluate_math_expression(payload: MathEvalInput):
    """Safely evaluate a mathematical expression string."""
    try:
        # Use simple_eval with defined safe functions and names
        result = simple_eval(payload.expression, functions=SAFE_FUNCTIONS, names=SAFE_NAMES)
        # Check if result is a valid number or boolean for the model
        if not isinstance(result, (int, float, bool)):
            return {"error": "Evaluation resulted in an unsupported type."}

        return {"result": result}
    except (NameNotDefined, FunctionNotDefined, InvalidExpression) as e:
        # Catch specific simpleeval errors
        return {"error": f"Invalid expression: {e}"}
    except Exception as e:
        # Catch other potential errors (e.g., division by zero within simpleeval)
        print(f"Error evaluating math expression: {e}")
        return {"error": f"Evaluation error: {e}"}
        # Or raise 500:
        # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during evaluation")
