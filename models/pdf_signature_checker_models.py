from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class VPathInfo(BaseModel):
    valid: bool
    validity_summary: str


class VSummary(BaseModel):
    intact: bool
    valid: bool
    trusted: bool
    expired: bool
    validity_summary: str
    trust_summary: str


class CertInfo(BaseModel):
    subject: str
    issuer: str
    serial: str
    valid_from: str
    valid_to: str


class SignatureValidationInfo(BaseModel):
    field_name: str
    validation_summary: VSummary
    signer_cert_info: Optional[CertInfo] = None
    ts_cert_info: Optional[CertInfo] = None  # Timestamping certificate
    validation_path_details: Optional[VPathInfo] = None
    raw_timestamp_info: Optional[Dict[str, Any]] = None
    signer_reported_timestamp: Optional[str] = None
    validation_errors: List[str] = []
    validation_warnings: List[str] = []


class PdfSignatureValidationOutput(BaseModel):
    filename: str
    is_signed: bool
    signature_count: int
    signatures: List[SignatureValidationInfo]
    processing_error: str | None = None
