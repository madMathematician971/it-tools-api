import io
import logging
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pyhanko.config.errors import ConfigurationError
from pyhanko.pdf_utils.misc import PdfReadError
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.general import SigningError, UnacceptableSignerError
from pyhanko.sign.validation import ValidationContext, validate_pdf_signature  # type: ignore
from pyhanko.sign.validation.errors import SignatureValidationError
from pyhanko.sign.validation.status import PdfSignatureStatus

from models.pdf_signature_checker_models import (
    CertInfo,
    PdfSignatureValidationOutput,
    SignatureValidationInfo,
    VPathInfo,
    VSummary,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pdf-signature", tags=["PDF Signature Checker"])

# --- Helper Functions ---


def format_cert_info(cert) -> CertInfo | None:
    if not cert:
        return None
    try:
        return CertInfo(
            subject=cert.subject.human_friendly,
            issuer=cert.issuer.human_friendly,
            serial=str(cert.serial_number),
            valid_from=cert.not_valid_before.isoformat(),
            valid_to=cert.not_valid_after.isoformat(),
        )
    except Exception as e:
        logger.error(f"Error formatting certificate info: {e}")
        return None


# --- Main Endpoint ---


@router.post(
    "/check-validated",
    response_model=PdfSignatureValidationOutput,
    summary="Validate digital signatures in a PDF file (integrity & basic trust)",
)
async def check_pdf_signature_validated(file: UploadFile = File(...)):
    """Reads a PDF file, finds digital signatures, and performs validation checks.

    - Verifies signature integrity (document not modified after signing).
    - Performs basic certificate path validation (without specific trust roots by default).
    - **Does NOT** guarantee the signer's identity is trusted unless trust roots are configured.
    """
    filename = file.filename or "uploaded_pdf"
    results: List[SignatureValidationInfo] = []
    error_msg = None
    signed = False
    count = 0

    try:
        pdf_content = await file.read()
        pdf_stream = io.BytesIO(pdf_content)
        reader = PdfFileReader(pdf_stream)
        embedded_signatures = reader.embedded_signatures

        signed = bool(embedded_signatures)
        count = len(embedded_signatures)

        if signed:
            logger.info(f"Found {count} embedded signatures in '{filename}'. Validating...")
            # Minimal context: don't trust any certs by default
            # To use system trust (more complex setup): use oscrypto_config or similar
            vc = ValidationContext(trust_roots=[])  # Empty list -> trust unknown

            for sig in embedded_signatures:
                validation_status: PdfSignatureStatus | None = None
                sig_info = None
                errors = []
                warnings = []
                try:
                    validation_status = validate_pdf_signature(sig, vc)

                    # Only process if validation_status is not None
                    if validation_status:
                        # Determine trust summary string based on properties
                        if validation_status.trusted:  # type: ignore
                            trust_summary_str = "Trusted"
                        elif validation_status.revoked:  # type: ignore
                            trust_summary_str = "Revoked"
                        else:
                            trust_summary_str = "Untrusted"  # Covers other untrusted cases

                        # Compile summary
                        summary = VSummary(
                            intact=validation_status.intact,
                            valid=validation_status.valid,
                            trusted=validation_status.trusted,  # type: ignore
                            expired=validation_status.expired,  # type: ignore
                            validity_summary=validation_status.summary(),
                            trust_summary=trust_summary_str,  # Use derived string
                        )

                        # Compile path details
                        path_details = None
                        if validation_status.path_validation_details:  # type: ignore
                            path_details = VPathInfo(
                                valid=validation_status.path_validation_details.valid,  # type: ignore
                                validity_summary=validation_status.path_validation_details.summary(),  # type: ignore
                            )

                        # Compile certificate info
                        signer_cert = None
                        if hasattr(validation_status, "signer_cert") and validation_status.signer_cert:  # type: ignore
                            signer_cert = format_cert_info(validation_status.signer_cert)  # type: ignore

                        ts_cert = None
                        if validation_status.timestamp_validation_details:  # type: ignore
                            ts_signer_cert = getattr(
                                validation_status.timestamp_validation_details, "signer_cert", None  # type: ignore
                            )
                            if ts_signer_cert:
                                ts_cert = format_cert_info(ts_signer_cert)

                        # Errors/Warnings from validation
                        errors.extend([str(e) for e in validation_status.errors])  # type: ignore
                        warnings.extend([str(w) for w in validation_status.warnings])  # type: ignore

                        sig_info = SignatureValidationInfo(
                            field_name=sig.field_name,
                            validation_summary=summary,
                            signer_cert_info=signer_cert,
                            ts_cert_info=ts_cert,
                            validation_path_details=path_details,
                            raw_timestamp_info=(
                                validation_status.timestamp_info.__dict__  # type: ignore
                                if hasattr(validation_status, "timestamp_info") and validation_status.timestamp_info  # type: ignore
                                else None
                            ),
                            signer_reported_timestamp=sig.sig_object.get("/M"),
                            validation_errors=errors,
                            validation_warnings=warnings,
                        )
                        results.append(sig_info)
                    else:
                        # Handle case where validation returns None (unexpected)
                        logger.error(f"Validation returned None for signature '{sig.field_name}'")
                        errors.append("Validation process failed unexpectedly.")
                        # Append a minimal error result
                        summary = VSummary(
                            intact=False,
                            valid=False,
                            trusted=False,
                            expired=True,
                            validity_summary="Validation Error",
                            trust_summary="Unknown",
                        )
                        results.append(
                            SignatureValidationInfo(
                                field_name=sig.field_name, validation_summary=summary, validation_errors=errors
                            )
                        )

                except (
                    SignatureValidationError,
                    SigningError,
                    UnacceptableSignerError,
                    ConfigurationError,
                ) as val_err:
                    logger.warning(
                        f"Validation failed for signature in field '{sig.field_name}' in '{filename}': {val_err}"
                    )
                    errors.append(f"Validation Error: {val_err}")
                    # Add a placeholder result indicating the failure
                    summary = VSummary(
                        intact=False,
                        valid=False,
                        trusted=False,
                        expired=True,
                        validity_summary="Validation Failed",
                        trust_summary="Unknown",
                    )
                    results.append(
                        SignatureValidationInfo(
                            field_name=sig.field_name,
                            validation_summary=summary,
                            validation_errors=errors,
                        )
                    )
                except Exception as gen_val_err:
                    logger.error(
                        f"Unexpected error during validation of signature '{sig.field_name}': {gen_val_err}",
                        exc_info=True,
                    )
                    errors.append(f"Unexpected Validation Error: {gen_val_err}")
                    summary = VSummary(
                        intact=False,
                        valid=False,
                        trusted=False,
                        expired=True,
                        validity_summary="Unexpected Error",
                        trust_summary="Unknown",
                    )
                    results.append(
                        SignatureValidationInfo(
                            field_name=sig.field_name,
                            validation_summary=summary,
                            validation_errors=errors,
                        )
                    )

    except PdfReadError as pdf_err:
        logger.info(f"Failed to read PDF '{filename}': {pdf_err}")
        error_msg = f"Failed to parse PDF file: {pdf_err}"
        # Use 400 for bad file format
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except Exception as e:
        logger.error(
            f"Error processing PDF file '{filename}' for signature validation: {e}",
            exc_info=True,
        )
        error_msg = f"Failed to process PDF file: {e}"
        # Use 500 for general processing errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg)
    finally:
        await file.close()

    return PdfSignatureValidationOutput(
        filename=filename,
        is_signed=signed,
        signature_count=count,
        signatures=results,
        processing_error=error_msg,
    )
