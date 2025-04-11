from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class QrErrorCorrectLevel(str, Enum):
    L = "L"  # Low (Approx 7% correction)
    M = "M"  # Medium (Approx 15% correction)
    Q = "Q"  # Quartile (Approx 25% correction)
    H = "H"  # High (Approx 30% correction)


class QrOutputFormat(str, Enum):
    svg = "svg"
    png = "png"  # Will be Base64 encoded
    # terminal = "terminal" # Could add terminal output


class QrCodeInput(BaseModel):
    text: str = Field(..., description="Text content to encode in the QR code")
    error_correction: QrErrorCorrectLevel = Field(
        QrErrorCorrectLevel.M, description="Error correction level (L, M, Q, H)"
    )
    output_format: QrOutputFormat = Field(QrOutputFormat.svg, description="Desired output format (svg, png)")
    # box_size: int = Field(10, description="Size of each box in pixels (for PNG)")
    # border: int = Field(4, description="Thickness of the border in boxes")
    # Add styling options if needed: fill_color, back_color


class QrCodeOutput(BaseModel):
    qr_code_data: str  # SVG string or Base64 PNG data
    output_format: QrOutputFormat
    error: Optional[str] = None


class WifiAuthType(str, Enum):
    WPA = "WPA"  # Includes WPA/WPA2
    WEP = "WEP"
    NOPASS = "nopass"  # Open network


class WifiQrCodeInput(BaseModel):
    ssid: str = Field(..., description="Network SSID (name).")
    password: Optional[str] = Field(None, description="Network password (required for WPA/WEP).")
    auth_type: WifiAuthType = Field(WifiAuthType.WPA, description="Authentication type (WPA, WEP, nopass).")
    hidden: bool = Field(False, description="Whether the SSID is hidden.")
    error_correction: QrErrorCorrectLevel = Field(
        QrErrorCorrectLevel.M,
        description="QR code error correction level (L, M, Q, H).",
    )
    output_format: QrOutputFormat = Field(QrOutputFormat.svg, description="Desired output format (svg, png).")
