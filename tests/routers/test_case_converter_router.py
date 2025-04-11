import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.case_converter_models import CaseConvertInput, CaseConvertOutput
from routers.case_converter_router import router as case_converter_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(case_converter_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Case Conversion ---


@pytest.mark.parametrize(
    "input_text, target_case, expected_output",
    [
        # Valid cases
        ("hello world", "camel", "helloWorld"),
        ("helloWorld", "snake", "hello_world"),
        ("hello_world", "pascal", "HelloWorld"),
        ("HelloWorld", "constant", "HELLO_WORLD"),
        ("HELLO_WORLD", "kebab", "hello-world"),
        ("hello-world", "capital", "Hello World"),  # Uses titlecase
        # Removed unsupported cases
        # ("hello-world", "dot", "hello.world"),
        # ("hello.world", "header", "Hello-World"),
        # ("Hello-World", "sentence", "Hello world"),
        # ("Hello world", "path", "hello/world"),
        ("hello world", "lower", "hello world"),
        ("hello world", "upper", "HELLO WORLD"),
        # Edge cases
        ("", "camel", ""),
        (" ", "snake", ""),
        ("  ", "pascal", ""),
        (" test ", "constant", "TEST"),
        (" test_string ", "kebab", "test-string"),
        ("123 numbers", "capital", "123 Numbers"),
        ("special-chars!", "lower", "special-chars!"),
        ("MiXeD CaSe", "upper", "MIXED CASE"),
    ],
)
def test_case_convert_valid(client: TestClient, input_text, target_case, expected_output):
    """Test successful case conversions."""
    payload = CaseConvertInput(input=input_text, target_case=target_case)
    response = client.post("/api/case/convert", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = CaseConvertOutput(**response.json())
    assert output.result == expected_output


@pytest.mark.asyncio
async def test_case_convert_invalid_case(client: TestClient):
    """Test case conversion with an invalid target case."""
    payload = CaseConvertInput(input="test string", target_case="invalid-case")
    response = client.post("/api/case/convert", json=payload.model_dump())

    # Expect 400 status code now that router exception handling is fixed
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # Check the specific detail message from the 400 HTTPException
    response_json = response.json()
    assert "detail" in response_json
    assert "Invalid target_case".lower() in response_json["detail"].lower()
