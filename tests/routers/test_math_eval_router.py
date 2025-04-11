import math

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.math_eval_models import MathEvalInput, MathEvalOutput
from routers.math_eval_router import router as math_eval_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(math_eval_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Math Evaluation ---


@pytest.mark.parametrize(
    "expression, expected_result",
    [
        # Basic arithmetic
        ("1 + 2", 3),
        ("10 - 4", 6),
        ("5 * 6", 30),
        ("100 / 4", 25.0),
        ("2 ** 8", 256),
        ("10 % 3", 1),
        ("-5", -5),
        ("+10", 10),
        ("1 + 2 * 3", 7),  # Operator precedence
        ("(1 + 2) * 3", 9),  # Parentheses
        # Floating point
        ("1.5 + 2.5", 4.0),
        ("pi * 2", math.pi * 2),
        ("e", math.e),
        # Safe functions
        ("sqrt(16)", 4.0),
        ("pow(2, 10)", 1024.0),
        ("sin(pi / 2)", 1.0),
        ("cos(0)", 1.0),
        ("abs(-10)", 10),
        ("floor(3.7)", 3),
        ("ceil(3.1)", 4),
        ("log10(100)", 2.0),
        # Safe names (constants)
        ("pi", math.pi),
        ("tau / 2", math.pi),
        ("e", math.e),
        ("true", True),
        ("false", False),
        # ('none', None), # simpleeval might not return None easily, API checks type
        # Boolean logic (simpleeval handles basic comparisons)
        ("1 < 2", True),
        ("5 > 10", False),
        ("1 <= 1", True),
        ("2 >= 3", False),
        ("1 == 1", True),
        ("1 != 2", True),
        # Note: simpleeval might not support 'and', 'or', 'not' directly
        # ("true and false", False), # Depends on simpleeval version/config
    ],
)
@pytest.mark.asyncio
async def test_evaluate_math_success(client: TestClient, expression: str, expected_result):
    """Test successful evaluation of various mathematical expressions."""
    payload = MathEvalInput(expression=expression)
    response = client.post("/api/math/evaluate", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = MathEvalOutput(**response.json())

    assert output.error is None
    # Handle potential float precision issues
    if isinstance(expected_result, float):
        assert isinstance(output.result, float)
        assert abs(output.result - expected_result) < 1e-9
    else:
        assert output.result == expected_result


@pytest.mark.parametrize(
    "expression, error_substring",
    [
        # Syntax errors
        ("1 +", "invalid syntax"),
        ("(* 2)", "cannot use starred expression"),
        ("1 + * 2", "invalid syntax"),
        # Undefined names/functions
        ("x + 1", "'x' is not defined"),
        ("undefined_func(10)", "Function 'undefined_func' not defined"),
        ("math.sqrt(4)", "'math' is not defined"),  # Direct module access disallowed
        ("import os", "Sorry, 'import' is not allowed"),
        ("__import__('os')", "Function '__import__' not defined"),  # Builtin import disallowed
        # Errors during evaluation
        ("1 / 0", "Evaluation error: division by zero"),
        ("log(-1)", "Evaluation error: math domain error"),
        ("sqrt(-4)", "Evaluation error: math domain error"),
        # Empty expression
        ("", "cannot evaluate empty string"),
    ],
)
@pytest.mark.asyncio
async def test_evaluate_math_failure(client: TestClient, expression: str, error_substring: str):
    """Test evaluation failures due to syntax errors, undefined names, or runtime errors."""
    payload = MathEvalInput(expression=expression)
    response = client.post("/api/math/evaluate", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK  # API returns 200 OK with error in body
    output = MathEvalOutput(**response.json())
    assert output.result is None
    assert output.error is not None
    # Check if the expected substring exists within the actual error message, case-insensitive
    assert error_substring.lower() in output.error.lower()
