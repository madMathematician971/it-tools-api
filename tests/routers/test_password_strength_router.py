import re  # Import re module

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.password_strength_models import (
    CrackTimeDisplay,
    CrackTimeSeconds,
    Feedback,
    PasswordInput,
    PasswordStrengthOutput,
)
from routers.password_strength_router import router as password_strength_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(password_strength_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Password Strength Check ---


@pytest.mark.parametrize(
    "password, expected_score_min, expected_score_max, expected_strength_pattern",
    [
        ("password", 0, 1, r"Weak|Very Weak"),
        ("P@ssword1", 1, 2, r"Weak|Fair"),
        ("CorrectHorseBatteryStaple", 3, 4, r"Good|Strong"),
        ("Tr0ub4dor&3", 3, 4, r"Good|Strong"),
        ("this is a very long and complex password with lots of words and symbols !@#$%^&*()", 4, 4, r"Strong"),
        ("a", 0, 0, r"Very Weak"),
        ("123456", 0, 1, r"Weak|Very Weak"),
    ],
)
@pytest.mark.asyncio
async def test_check_password_strength_scores(
    client: TestClient, password: str, expected_score_min: int, expected_score_max: int, expected_strength_pattern: str
):
    """Test password strength check returns expected score range and strength description."""
    payload = PasswordInput(password=password)
    response = client.post("/api/password-strength/check", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = PasswordStrengthOutput(**response.json())

    assert output.password == password
    assert output.score >= expected_score_min
    assert output.score <= expected_score_max
    assert isinstance(output.entropy, float)
    assert output.entropy > 0 or password == ""  # Entropy should be positive
    assert isinstance(output.calc_time, int)
    assert output.calc_time >= 0
    assert isinstance(output.crack_time_seconds, CrackTimeSeconds)
    assert isinstance(output.crack_time_display, CrackTimeDisplay)
    assert isinstance(output.feedback, Feedback)
    assert isinstance(output.matches, list)
    assert isinstance(output.strength, str)
    assert len(output.strength) > 0
    assert re.match(expected_strength_pattern, output.strength)

    # Optional: Compare with direct zxcvbn call for more detailed validation
    # direct_result = zxcvbn(password)
    # assert output.score == direct_result.get('score')
    # Add more detailed comparisons if necessary


@pytest.mark.asyncio
async def test_check_password_strength_empty(client: TestClient):
    """Test password strength check with an empty password."""
    payload = PasswordInput(password="")
    response = client.post("/api/password-strength/check", json=payload.model_dump())
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Password cannot be empty" in response.json()["detail"]


@pytest.mark.asyncio
async def test_check_password_strength_feedback(client: TestClient):
    """Test that feedback (warning/suggestions) is present for weak passwords."""
    weak_password = "12345"
    payload = PasswordInput(password=weak_password)
    response = client.post("/api/password-strength/check", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = PasswordStrengthOutput(**response.json())

    assert output.score <= 1  # Expect weak score
    assert output.feedback is not None
    # Check if either warning or suggestions are populated for weak passwords
    assert output.feedback.warning or output.feedback.suggestions
    if output.feedback.warning:
        assert isinstance(output.feedback.warning, str)
        assert len(output.feedback.warning) > 0
    if output.feedback.suggestions:
        assert isinstance(output.feedback.suggestions, list)
        assert len(output.feedback.suggestions) > 0
        assert all(isinstance(s, str) for s in output.feedback.suggestions)
