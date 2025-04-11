import base64
import io
import logging  # Add logging import
from typing import Optional

import qrcode
import qrcode.image.svg  # For SVG output
from fastapi import APIRouter, HTTPException, Response, status

from models.qrcode_models import (
    QrCodeInput,
    QrCodeOutput,
    QrErrorCorrectLevel,
    QrOutputFormat,
    WifiAuthType,
    WifiQrCodeInput,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/qrcode", tags=["QR Code"])

# Map model enum to library constants
ERROR_CORRECT_MAP = {
    QrErrorCorrectLevel.L: qrcode.constants.ERROR_CORRECT_L,
    QrErrorCorrectLevel.M: qrcode.constants.ERROR_CORRECT_M,
    QrErrorCorrectLevel.Q: qrcode.constants.ERROR_CORRECT_Q,
    QrErrorCorrectLevel.H: qrcode.constants.ERROR_CORRECT_H,
}


@router.post("/generate")  # Output depends on format, handled manually
async def generate_qr_code(payload: QrCodeInput):
    """Generate a QR code image (SVG or PNG)."""
    try:
        qr = qrcode.QRCode(
            version=None,  # Auto-detect version
            error_correction=ERROR_CORRECT_MAP.get(payload.error_correction, qrcode.constants.ERROR_CORRECT_M),
            box_size=10,  # Default, can be made configurable
            border=4,  # Default, can be made configurable
        )
        qr.add_data(payload.text)
        qr.make(fit=True)

        img_buffer = io.BytesIO()
        output_format = payload.output_format

        if output_format == QrOutputFormat.svg:
            # Use SVG factory
            img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
            img.save(img_buffer)
            svg_data = img_buffer.getvalue().decode("utf-8")
            # Return SVG directly with appropriate media type
            return Response(content=svg_data, media_type="image/svg+xml")

        elif output_format == QrOutputFormat.png:
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(img_buffer, format="PNG")
            png_data_b64 = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
            # Return Base64 PNG data in a JSON structure
            return QrCodeOutput(qr_code_data=png_data_b64, output_format=output_format)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported output format requested.",
            )

    except Exception as e:
        print(f"Error generating QR code: {e}")
        # Return error within a JSON structure if possible
        return QrCodeOutput(
            qr_code_data="",
            output_format=payload.output_format,
            error=f"Failed to generate QR code: {e}",
        )
        # Or raise 500:
        # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during QR code generation")


# --- WiFi QR Code Endpoint ---


def format_wifi_string(ssid: str, auth_type: WifiAuthType, password: Optional[str], hidden: bool) -> str:
    "Formats the special WIFI: string for QR codes."

    # Escape special characters: \, ;, ,, ", :
    def escape_wifi_value(value: str) -> str:
        if not value:
            return ""
        return (
            value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace('"', '\\"').replace(":", "\\:")
        )

    escaped_ssid = escape_wifi_value(ssid)
    escaped_password = escape_wifi_value(password or "")

    # Determine authentication string for WIFI: format
    auth_str = "WPA"  # Default for WPA/WPA2
    if auth_type == WifiAuthType.WEP:
        auth_str = "WEP"
    elif auth_type == WifiAuthType.NOPASS:
        auth_str = "nopass"
        escaped_password = ""  # No password for nopass

    if auth_type != WifiAuthType.NOPASS and not password:
        raise ValueError("Password is required for WPA and WEP authentication types.")

    hidden_str = "true" if hidden else "false"

    # Format: WIFI:T:<auth_type>;S:<ssid>;P:<password>;H:<hidden>;;
    return f"WIFI:T:{auth_str};S:{escaped_ssid};P:{escaped_password};H:{hidden_str};;"


@router.post("/generate-wifi")  # Similar output structure to /generate
async def generate_wifi_qr_code(payload: WifiQrCodeInput):
    """Generate a QR code for connecting to a WiFi network.

    Takes SSID, password, auth type, hidden status and generates the appropriate QR code.
    """
    try:
        # Format the WIFI string
        try:
            wifi_string = format_wifi_string(
                ssid=payload.ssid,
                auth_type=payload.auth_type,
                password=payload.password,
                hidden=payload.hidden,
            )
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

        logger.info(f"Generating WiFi QR code for SSID: {payload.ssid}")

        # --- Reuse QR generation logic --- (Copied and adapted from /generate)
        qr = qrcode.QRCode(
            version=None,  # Auto-detect version
            error_correction=ERROR_CORRECT_MAP.get(payload.error_correction, qrcode.constants.ERROR_CORRECT_M),
            box_size=10,  # Default, can be made configurable
            border=4,  # Default, can be made configurable
        )
        qr.add_data(wifi_string)
        qr.make(fit=True)

        img_buffer = io.BytesIO()
        output_format = payload.output_format

        if output_format == QrOutputFormat.svg:
            img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
            img.save(img_buffer)
            svg_data = img_buffer.getvalue().decode("utf-8")
            return Response(content=svg_data, media_type="image/svg+xml")

        elif output_format == QrOutputFormat.png:
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(img_buffer, format="PNG")
            png_data_b64 = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
            return QrCodeOutput(qr_code_data=png_data_b64, output_format=output_format)
        else:
            # Should be caught by Pydantic, but safeguard
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported output format requested.",
            )
        # --- End reused logic ---

    except HTTPException as http_exc:
        raise http_exc  # Re-raise validation errors
    except Exception as e:
        logger.error(
            f"Error generating WiFi QR code for SSID '{payload.ssid}': {e}",
            exc_info=True,
        )
        # Return error within a JSON structure for PNG, maybe raise 500 for SVG?
        if payload.output_format == QrOutputFormat.png:
            return QrCodeOutput(
                qr_code_data="",
                output_format=payload.output_format,
                error=f"Failed to generate WiFi QR code: {e}",
            )
        else:  # For SVG or unexpected format errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error during WiFi QR code generation: {str(e)}",
            )
