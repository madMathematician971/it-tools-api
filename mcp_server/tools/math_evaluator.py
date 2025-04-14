"""
Math expression evaluator tool for MCP server.
"""

import math

from simpleeval import FunctionNotDefined, InvalidExpression, NameNotDefined, simple_eval

from mcp_server import mcp_app

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


@mcp_app.tool()
def evaluate_math(expression: str) -> dict:
    """
    Safely evaluate a mathematical expression.

    Args:
        expression: The math expression to evaluate

    Returns:
        A dictionary containing:
            result: The evaluation result (number or boolean)
            error: Optional error message if evaluation fails
    """
    try:
        # Use simple_eval with defined safe functions and names
        result = simple_eval(expression, functions=SAFE_FUNCTIONS, names=SAFE_NAMES)

        # Check if result is a valid number or boolean for the model
        if not isinstance(result, (int, float, bool, type(None))):
            return {"result": None, "error": "Evaluation resulted in an unsupported type."}

        return {"result": result, "error": None}
    except (NameNotDefined, FunctionNotDefined, InvalidExpression) as e:
        # Catch specific simpleeval errors
        return {"result": None, "error": f"Invalid expression: {e}"}
    except Exception as e:
        # Catch other potential errors (e.g., division by zero within simpleeval)
        return {"result": None, "error": f"Evaluation error: {e}"}
