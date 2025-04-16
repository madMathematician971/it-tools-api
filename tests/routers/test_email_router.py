import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.email_models import EmailInput, EmailNormalizeOutput
from routers.email_router import router as email_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(email_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Email Normalization ---


@pytest.mark.parametrize(
    "input_email, expected_normalized_email",
    [
        # Gmail/Google rules
        ("test.email@gmail.com", "testemail@gmail.com"),
        ("test.email+alias@gmail.com", "testemail@gmail.com"),
        ("Test.Email@googlemail.com", "testemail@googlemail.com"),  # Case and dot
        ("testemail+other@google.com", "testemail@google.com"),
        ("testemail@gmail.com", "testemail@gmail.com"),  # Already normalized
        # Outlook/Hotmail/Live rules
        ("test.email@outlook.com", "test.email@outlook.com"),  # Dots are significant
        ("test.email+alias@outlook.com", "test.email@outlook.com"),
        ("TestEmail+tag@hotmail.com", "testemail@hotmail.com"),  # Case insensitivity
        ("testemail+other@live.com", "testemail@live.com"),
        # Other domains (no specific rules applied, just lowercase)
        ("Test.Email@example.com", "test.email@example.com"),
        ("test+alias@example.com", "test+alias@example.com"),
        ("UPPERCASE@DOMAIN.NET", "uppercase@domain.net"),
        # Edge cases
        ("test@gmail.com", "test@gmail.com"),
    ],
)
@pytest.mark.asyncio
async def test_email_normalize_success(client: TestClient, input_email: str, expected_normalized_email: str):
    """Test successful email normalization based on provider rules."""
    payload = EmailInput(email=input_email)
    response = client.post("/api/email/normalize", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = EmailNormalizeOutput(**response.json())
    assert output.normalized_email == expected_normalized_email
    assert output.original_email == input_email  # Ensure original is preserved


@pytest.mark.parametrize(
    "invalid_email",
    [
        "plainaddress",
        "#@%^%#$@#$@#.com",
        "@example.com",
        "Joe Smith <email@example.com>",
        "email.example.com",
        "email@example@example.com",
        ".email@example.com",
        "email.@example.com",
        "email..email@example.com",
        "email@example.com (Joe Smith)",
        "email@example..com",
        "Abc..123@example.com",
        "test.+.@gmail.com",  # Invalid due to trailing dot before @
        "",  # Empty string
    ],
)
@pytest.mark.asyncio
async def test_email_normalize_invalid_format(client: TestClient, invalid_email: str):
    """Test email normalization with invalid email formats."""
    payload = EmailInput(email=invalid_email)
    response = client.post("/api/email/normalize", json=payload.model_dump())

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Map specific invalid inputs to their expected error details
    expected_details = {
        "plainaddress": "Invalid input: Invalid email format.",
        "#@%^%#$@#$@#.com": "Invalid input: Invalid email format.",
        "@example.com": "Invalid input: Invalid email format.",
        "Joe Smith <email@example.com>": "Invalid input: Invalid email format.",
        "email.example.com": "Invalid input: Invalid email format.",
        "email@example@example.com": "Invalid input: Invalid email format.",
        "": "Invalid input: Invalid email format.",
        ".email@example.com": "Invalid input: Invalid email characters or structure.",
        "email.@example.com": "Invalid input: Invalid email characters or structure.",
        "email..email@example.com": "Invalid input: Invalid email characters or structure.",
        "email@example.com (Joe Smith)": "Invalid input: Invalid email format.",
        "email@example..com": "Invalid input: Invalid email characters or structure.",
        "Abc..123@example.com": "Invalid input: Invalid email characters or structure.",
        "test.+.@gmail.com": "Invalid input: Invalid email characters or structure.",
    }

    expected_detail = expected_details.get(invalid_email)
    if expected_detail is None:
        pytest.fail(f"Test case '{invalid_email}' not found in expected details map.")

    assert response.json()["detail"] == expected_detail
