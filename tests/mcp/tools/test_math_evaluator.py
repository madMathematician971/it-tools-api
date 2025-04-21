"""
Unit tests for the math_evaluator tool.
"""

import math

from mcp_server.tools.math_evaluator import SAFE_FUNCTIONS, SAFE_NAMES, evaluate_math

# --- Test Successful Math Evaluations ---


def test_basic_arithmetic():
    """Test basic arithmetic operations."""
    # Addition
    assert evaluate_math(expression="2 + 2")["result"] == 4

    # Subtraction
    assert evaluate_math(expression="10 - 5")["result"] == 5

    # Multiplication
    assert evaluate_math(expression="3 * 4")["result"] == 12

    # Division
    assert evaluate_math(expression="10 / 2")["result"] == 5

    # Integer division
    assert evaluate_math(expression="7 // 2")["result"] == 3

    # Modulo
    assert evaluate_math(expression="7 % 3")["result"] == 1

    # Exponentiation
    assert evaluate_math(expression="2 ** 3")["result"] == 8

    # Combined operations with order of operations
    assert evaluate_math(expression="2 + 3 * 4")["result"] == 14
    assert evaluate_math(expression="(2 + 3) * 4")["result"] == 20


def test_math_functions():
    """Test mathematical functions."""

    # Round result to handle floating point precision issues
    def round_result(expr, places=10):
        result = evaluate_math(expression=expr)["result"]
        if isinstance(result, float):
            return round(result, places)
        return result

    # Trigonometric functions
    assert round_result("sin(0)") == 0
    assert round_result("cos(0)") == 1
    assert round_result("tan(0)") == 0

    # Inverse trigonometric functions
    assert round_result("asin(0)") == 0
    assert round_result("acos(1)") == 0
    assert round_result("atan(0)") == 0

    # Hyperbolic functions
    assert round_result("sinh(0)") == 0
    assert round_result("cosh(0)") == 1
    assert round_result("tanh(0)") == 0

    # Exponentiation and logarithms
    assert round_result("exp(0)") == 1
    assert round_result("log(1)") == 0
    assert round_result("log10(10)") == 1
    assert round_result("sqrt(9)") == 3

    # Absolute value
    assert round_result("abs(-5)") == 5

    # Floor and ceiling
    assert round_result("floor(3.7)") == 3
    assert round_result("ceil(3.2)") == 4


def test_constants():
    """Test mathematical constants."""
    # Pi
    pi_result = evaluate_math(expression="pi")["result"]
    assert math.isclose(pi_result, math.pi)

    # e (Euler's number)
    e_result = evaluate_math(expression="e")["result"]
    assert math.isclose(e_result, math.e)

    # tau (2*pi)
    tau_result = evaluate_math(expression="tau")["result"]
    assert math.isclose(tau_result, math.tau)


def test_boolean_expressions():
    """Test boolean expressions."""
    # Comparisons
    assert evaluate_math(expression="2 > 1")["result"] is True
    assert evaluate_math(expression="2 < 1")["result"] is False
    assert evaluate_math(expression="2 >= 2")["result"] is True
    assert evaluate_math(expression="2 <= 1")["result"] is False
    assert evaluate_math(expression="2 == 2")["result"] is True
    assert evaluate_math(expression="2 != 2")["result"] is False

    # Boolean constants
    assert evaluate_math(expression="true")["result"] is True
    assert evaluate_math(expression="false")["result"] is False

    # Boolean operators
    assert evaluate_math(expression="true and true")["result"] is True
    assert evaluate_math(expression="true and false")["result"] is False
    assert evaluate_math(expression="true or false")["result"] is True
    assert evaluate_math(expression="false or false")["result"] is False
    assert evaluate_math(expression="not true")["result"] is False
    assert evaluate_math(expression="not false")["result"] is True


def test_complex_expressions():
    """Test more complex mathematical expressions."""
    # Complex arithmetic
    assert evaluate_math(expression="2 * (3 + 4) / 2")["result"] == 7

    # Nested functions
    sin_pi_result = evaluate_math(expression="sin(pi)")["result"]
    assert abs(sin_pi_result) < 1e-15  # Should be very close to 0

    # Expression with multiple functions
    expr = "sqrt(pow(3, 2) + pow(4, 2))"  # Pythagorean theorem
    assert evaluate_math(expression=expr)["result"] == 5

    # Complex boolean logic
    expr = "(2 > 1 and 3 > 2) or (5 < 4)"
    assert evaluate_math(expression=expr)["result"] is True


# --- Test Error Cases ---


def test_invalid_syntax():
    """Test expressions with invalid syntax."""
    # Missing closing parenthesis
    result = evaluate_math(expression="(2 + 3 * 4")
    assert result["result"] is None
    assert result["error"] is not None

    # Double operators
    result = evaluate_math(expression="2 ++ 3")
    assert result["result"] == 5
    assert result["error"] is None


def test_undefined_variables():
    """Test expressions with undefined variables."""
    # Undefined variable
    result = evaluate_math(expression="x + 5")
    assert result["result"] is None
    assert result["error"] is not None
    assert "'x' is not defined" in result["error"].lower()


def test_undefined_functions():
    """Test expressions with undefined functions."""
    # Function not in the safe list
    result = evaluate_math(expression="fibonacci(5)")
    assert result["result"] is None
    assert result["error"] is not None
    assert "FunctionNotDefined" in result["error"] or "function" in result["error"].lower()


def test_division_by_zero():
    """Test division by zero."""
    result = evaluate_math(expression="1/0")
    assert result["result"] is None
    assert result["error"] is not None
    assert "division by zero" in result["error"].lower()


def test_domain_errors():
    """Test mathematical domain errors."""
    # Square root of a negative number
    result = evaluate_math(expression="sqrt(-1)")
    assert result["result"] is None
    assert result["error"] is not None

    # Logarithm of zero or negative number
    result = evaluate_math(expression="log(0)")
    assert result["result"] is None
    assert result["error"] is not None

    # Inverse sine of value outside [-1, 1]
    result = evaluate_math(expression="asin(2)")
    assert result["result"] is None
    assert result["error"] is not None


# --- Verify Available Functions and Constants ---


def test_all_safe_functions_available():
    """Test that all functions listed in SAFE_FUNCTIONS are actually available."""
    for func_name in SAFE_FUNCTIONS:
        # Create a simple expression using this function with a safe argument
        if func_name == "atan2":
            expr = f"{func_name}(1, 0)"  # atan2 requires two arguments
        elif func_name == "fmod":
            expr = f"{func_name}(5, 2)"  # fmod requires two arguments
        elif func_name == "ldexp":
            expr = f"{func_name}(1, 0)"  # ldexp requires two arguments
        elif func_name == "pow":
            expr = f"{func_name}(2, 3)"  # pow requires two arguments
        elif func_name in ["asin", "acos"]:
            # These functions require arguments in range [-1, 1]
            expr = f"{func_name}(0)"
        elif func_name in ["log", "log10"]:
            # These functions require positive arguments
            expr = f"{func_name}(1)"
        else:
            # Use 0 as a generic argument
            expr = f"{func_name}(0)"

        result = evaluate_math(expression=expr)

        # Handle functions that return tuples (unsupported by evaluate_math wrapper)
        if func_name in ["frexp", "modf"]:
            assert result["error"] is not None, f"Function {func_name} should return tuple, handled as error"
            assert "unsupported type" in result["error"], f"Function {func_name} error should mention unsupported type"
        else:
            assert result["error"] is None, f"Function {func_name} should be available and return supported type"


def test_all_safe_constants_available():
    """Test that all constants listed in SAFE_NAMES are actually available."""
    for const_name in SAFE_NAMES:
        result = evaluate_math(expression=const_name)
        assert result["error"] is None, f"Constant {const_name} should be available"


# --- Edge Cases ---


def test_empty_expression():
    """Test evaluating an empty expression."""
    result = evaluate_math(expression="")
    assert result["result"] is None
    assert result["error"] is not None


def test_whitespace_only_expression():
    """Test evaluating a whitespace-only expression."""
    result = evaluate_math(expression="   ")
    assert result["result"] is None
    assert result["error"] is not None


def test_very_large_numbers():
    """Test expressions that result in very large numbers."""
    # Large exponentiation (should work but produce a large number)
    result = evaluate_math(expression="2 ** 100")
    assert result["result"] == 2**100
    assert result["error"] is None

    # Even larger exponentiation that might cause issues in some systems
    result = evaluate_math(expression="2 ** 1000")
    assert result["result"] == 2**1000
    assert result["error"] is None
