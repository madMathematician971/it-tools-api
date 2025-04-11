import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.iban_models import IbanInput, IbanValidationOutput
from routers.iban_router import router as iban_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(iban_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test IBAN Validation ---


@pytest.mark.parametrize(
    "iban_string, expected_is_valid, expected_country, expected_checksum, expected_bban, expected_formatted",
    [
        # Valid IBANs (replace with real examples if possible, these are illustrative)
        (
            "DE89370400440532013000",
            True,
            "DE",
            "89",
            "370400440532013000",
            "DE89 3704 0044 0532 0130 00",
        ),
        (
            "GB29NWBK60161331926819",
            True,
            "GB",
            "29",
            "NWBK60161331926819",
            "GB29 NWBK 6016 1331 9268 19",
        ),
        (
            "FR1420041010050500013M02606",
            True,
            "FR",
            "14",
            "20041010050500013M02606",
            "FR14 2004 1010 0505 0001 3M02 606",
        ),
        # IBAN with spaces (should be handled by schwifty)
        (
            "DE89 3704 0044 0532 0130 00",
            True,
            "DE",
            "89",
            "370400440532013000",
            "DE89 3704 0044 0532 0130 00",
        ),
        # Lowercase IBAN (should be handled by schwifty)
        (
            "gb29nwbk60161331926819",
            True,
            "GB",
            "29",
            "NWBK60161331926819",
            "GB29 NWBK 6016 1331 9268 19",
        ),
    ],
)
@pytest.mark.asyncio
async def test_validate_iban_success(
    client: TestClient,
    iban_string: str,
    expected_is_valid: bool,
    expected_country: str,
    expected_checksum: str,
    expected_bban: str,
    expected_formatted: str,
):
    """Test successful IBAN validation and parsing."""
    payload = IbanInput(iban_string=iban_string)
    response = client.post("/api/iban/validate", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = IbanValidationOutput(**response.json())

    assert output.is_valid == expected_is_valid
    assert output.error is None
    assert output.country_code == expected_country
    assert output.check_digits == expected_checksum
    assert output.bban == expected_bban
    assert output.iban_string_formatted == expected_formatted


@pytest.mark.parametrize(
    "invalid_iban_string, expected_error_substring",
    [
        # Invalid checksum
        ("DE88370400440532013000", "invalid checksum digits"),
        # Invalid length for country
        ("DE8937040044053201300", "invalid iban length"),
        # Invalid country code
        ("XX89370400440532013000", "unknown country-code"),
        # Invalid characters / BBAN structure
        ("DE89!70400440532013000", "invalid bban structure"),
        # Invalid structure (BBAN)
        ("GB29NWBK6016133192681X", "invalid bban structure"),
        # Empty string
        ("", "invalid characters in iban"),
    ],
)
@pytest.mark.asyncio
async def test_validate_iban_failure(client: TestClient, invalid_iban_string: str, expected_error_substring: str):
    """Test validation failures for various invalid IBANs."""
    payload = IbanInput(iban_string=invalid_iban_string)
    response = client.post("/api/iban/validate", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK  # API returns 200 OK with is_valid=False
    output = IbanValidationOutput(**response.json())

    assert output.is_valid is False
    assert output.error is not None
    assert expected_error_substring in output.error.lower()  # Check case-insensitively
    assert output.country_code is None
    assert output.check_digits is None
    assert output.bban is None
    assert output.iban_string_formatted is None
