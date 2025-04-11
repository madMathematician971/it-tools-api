import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from pyhanko.pdf_utils.misc import PdfReadError
from pyhanko.sign.validation.errors import SignatureValidationError

from models.pdf_signature_checker_models import PdfSignatureValidationOutput, SignatureValidationInfo
from routers.pdf_signature_checker_router import router as pdf_checker_router


# Mock classes from pyhanko because installing it fully might be complex in test env
# We only need the structure for type hinting and mocking.
class MockPdfFileReader:
    embedded_signatures = []

    def __init__(self, stream):
        pass


class MockEmbeddedPdfSignature:
    field_name: str = "Signature1"
    sig_object: dict = {"/M": "D:20230101120000Z"}  # Example signing time


class MockCert:
    subject = MagicMock()
    issuer = MagicMock()
    serial_number = 12345
    not_valid_before = MagicMock()
    not_valid_after = MagicMock()

    def __init__(self):
        self.subject.human_friendly = "CN=Test Signer"
        self.issuer.human_friendly = "CN=Test CA"
        self.not_valid_before.isoformat.return_value = "2023-01-01T00:00:00"
        self.not_valid_after.isoformat.return_value = "2025-01-01T00:00:00"


class MockPathValidationDetails:
    valid = True
    signer_cert = MockCert()

    def summary(self):
        return "Path OK"


class MockValidationStatus:
    intact: bool = True
    valid: bool = True
    trusted: bool = False  # Usually false without trust roots
    expired: bool = False
    revoked: bool = False
    signer_cert: MockCert | None = None
    timestamp_validation_details = None
    path_validation_details: MockPathValidationDetails | None = None
    errors = []
    warnings = []
    timestamp_info = None

    def summary(self):
        return "OK"

    def trust_summary(self):
        return "UNKNOWN"


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(pdf_checker_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test PDF Signature Check ---


@patch("routers.pdf_signature_checker_router.PdfFileReader", MockPdfFileReader)
@patch("routers.pdf_signature_checker_router.validate_pdf_signature")
@pytest.mark.asyncio
async def test_check_pdf_signed_and_valid(mock_validate, client: TestClient):
    """Test checking a PDF with one valid (but untrusted) signature."""
    # Setup mock validation result
    mock_path_details = MockPathValidationDetails()
    mock_status = MockValidationStatus()
    mock_status.path_validation_details = mock_path_details
    mock_status.signer_cert = mock_path_details.signer_cert
    mock_validate.return_value = mock_status

    # Setup mock PDF reader
    MockPdfFileReader.embedded_signatures = [MockEmbeddedPdfSignature()]

    # Prepare dummy file upload
    dummy_pdf_content = b"%PDF-1.4\n...dummy content..."
    file_obj = io.BytesIO(dummy_pdf_content)

    response = client.post(
        "/api/pdf-signature/check-validated", files={"file": ("test.pdf", file_obj, "application/pdf")}
    )

    assert response.status_code == status.HTTP_200_OK
    output = PdfSignatureValidationOutput(**response.json())

    assert output.is_signed is True
    assert output.signature_count == 1
    assert output.processing_error is None
    assert len(output.signatures) == 1

    sig_result = output.signatures[0]
    assert isinstance(sig_result, SignatureValidationInfo)
    assert sig_result.field_name == "Signature1"
    assert sig_result.validation_summary.intact is True
    assert sig_result.validation_summary.valid is True
    assert sig_result.validation_summary.trusted is False  # Expected without trust roots
    assert sig_result.signer_cert_info is not None
    assert sig_result.signer_cert_info.subject == "CN=Test Signer"
    assert not sig_result.validation_errors
    assert not sig_result.validation_warnings
    mock_validate.assert_called_once()


@patch("routers.pdf_signature_checker_router.PdfFileReader", MockPdfFileReader)
@patch("routers.pdf_signature_checker_router.validate_pdf_signature")
@pytest.mark.asyncio
async def test_check_pdf_unsigned(mock_validate, client: TestClient):
    """Test checking a PDF file with no signatures."""
    MockPdfFileReader.embedded_signatures = []  # No signatures
    dummy_pdf_content = b"%PDF-1.4\n...unsigned..."
    file_obj = io.BytesIO(dummy_pdf_content)

    response = client.post(
        "/api/pdf-signature/check-validated", files={"file": ("unsigned.pdf", file_obj, "application/pdf")}
    )

    assert response.status_code == status.HTTP_200_OK
    output = PdfSignatureValidationOutput(**response.json())

    assert output.is_signed is False
    assert output.signature_count == 0
    assert output.processing_error is None
    assert len(output.signatures) == 0
    mock_validate.assert_not_called()


@patch("routers.pdf_signature_checker_router.PdfFileReader", MockPdfFileReader)
@patch("routers.pdf_signature_checker_router.validate_pdf_signature")
@pytest.mark.asyncio
async def test_check_pdf_signature_invalid(mock_validate, client: TestClient):
    """Test checking a PDF where the signature validation fails."""
    # Setup mock validation to raise an error
    mock_validate.side_effect = SignatureValidationError("Integrity check failed")

    # Setup mock PDF reader
    MockPdfFileReader.embedded_signatures = [MockEmbeddedPdfSignature()]

    dummy_pdf_content = b"%PDF-1.4\n...tampered..."
    file_obj = io.BytesIO(dummy_pdf_content)

    response = client.post(
        "/api/pdf-signature/check-validated", files={"file": ("tampered.pdf", file_obj, "application/pdf")}
    )

    assert response.status_code == status.HTTP_200_OK  # API handles validation errors gracefully
    output = PdfSignatureValidationOutput(**response.json())

    assert output.is_signed is True
    assert output.signature_count == 1
    assert output.processing_error is None
    assert len(output.signatures) == 1

    sig_result = output.signatures[0]
    assert sig_result.validation_summary.valid is False
    assert sig_result.validation_summary.intact is False
    assert sig_result.validation_summary.validity_summary == "Validation Failed"
    assert sig_result.validation_errors is not None
    assert len(sig_result.validation_errors) > 0
    assert "Integrity check failed" in sig_result.validation_errors[0]
    mock_validate.assert_called_once()


@patch("routers.pdf_signature_checker_router.PdfFileReader")
@pytest.mark.asyncio
async def test_check_pdf_read_error(mock_reader, client: TestClient):
    """Test checking a file that is not a valid PDF."""
    # Mock PdfFileReader to raise an error
    mock_reader.side_effect = PdfReadError("Invalid PDF header")

    dummy_content = b"This is not a PDF file."
    file_obj = io.BytesIO(dummy_content)

    response = client.post(
        "/api/pdf-signature/check-validated", files={"file": ("invalid.txt", file_obj, "text/plain")}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Failed to parse PDF file" in response.json()["detail"]
    assert "Invalid PDF header" in response.json()["detail"]
