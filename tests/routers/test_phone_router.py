import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

# Assuming models are defined or imported correctly
from models.phone_models import PhoneInput, PhoneOutput
from routers.phone_router import router as phone_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(phone_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Phone Number Parsing ---


@pytest.mark.parametrize(
    "phone_number_string, default_country, expected",
    [
        # Valid US Number (with country hint)
        (
            "(800) 555-1212",
            "US",
            {
                "is_valid": True,
                "country_code": 1,
                "national_number": "8005551212",
                "e164_format": "+18005551212",
                "national_format": "(800) 555-1212",
                "international_format": "+1 800-555-1212",
                "error": None,
            },
        ),
        # Valid US Number (E164 format, no hint needed)
        (
            "+1 800-555-1212",
            None,
            {
                "is_valid": True,
                "country_code": 1,
                "national_number": "8005551212",
                "e164_format": "+18005551212",
                "national_format": "(800) 555-1212",
                "international_format": "+1 800-555-1212",
                "error": None,
            },
        ),
        # Valid UK Number (with country hint)
        (
            "020 7123 4567",
            "GB",
            {
                "is_valid": True,
                "country_code": 44,
                "national_number": "2071234567",
                "e164_format": "+442071234567",
                "national_format": "020 7123 4567",
                "international_format": "+44 20 7123 4567",
                "error": None,
            },
        ),
        # Valid UK Number (International format)
        (
            "+44 20 7123 4567",
            None,
            {
                "is_valid": True,
                "country_code": 44,
                "national_number": "2071234567",
                "e164_format": "+442071234567",
                "national_format": "020 7123 4567",
                "international_format": "+44 20 7123 4567",
                "error": None,
            },
        ),
        # Number requiring hint to be valid
        (
            "555-1212",
            "US",
            {
                "is_valid": False,  # Often not valid without area code
                "error": "Number is not valid.",
                # Other fields might be None or based on partial parse
            },
        ),
        # Number parseable but invalid (e.g., too short/long for country)
        (
            "+1 800 555 123",
            "US",
            {
                "is_valid": False,
                "error": "Number is not valid.",
                "country_code": None,
                # Other fields might be partially filled
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_parse_phone_number_success_and_validity(
    client: TestClient, phone_number_string: str, default_country: str | None, expected: dict
):
    """Test parsing valid and invalid (but parseable) phone numbers."""
    payload = PhoneInput(phone_number_string=phone_number_string, default_country=default_country)
    response = client.post("/api/phone/parse", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output_dict = response.json()
    # Only compare the keys present in the expected dictionary
    for key, value in expected.items():
        assert output_dict.get(key) == value, f"Mismatch on key: {key}"


@pytest.mark.parametrize(
    "phone_number_string, default_country, error_substring",
    [
        ("not a number", None, "Parsing failed"),
        ("+1 123 456 789a", None, "Number is not valid."),
        ("", None, "Parsing failed"),
    ],
)
@pytest.mark.asyncio
async def test_parse_phone_number_parse_error(
    client: TestClient, phone_number_string: str, default_country: str | None, error_substring: str
):
    """Test inputs that should cause a NumberParseException or be invalid."""
    payload = PhoneInput(phone_number_string=phone_number_string, default_country=default_country)
    response = client.post("/api/phone/parse", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = PhoneOutput(**response.json())
    assert output.is_valid is False
    assert output.error is not None
    # Check for the expected error message (case-insensitive)
    assert error_substring.lower() in output.error.lower()
