import base64

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.qrcode_models import (
    QrCodeInput,
    QrCodeOutput,
    QrErrorCorrectLevel,
    QrOutputFormat,
    WifiAuthType,
    WifiQrCodeInput,
)
from routers.qrcode_router import router as qrcode_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(qrcode_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test QR Code Generation (Text) ---


@pytest.mark.parametrize(
    "text, error_correction, output_format, expected_content_type, check_base64",
    [
        ("Hello QR Code", QrErrorCorrectLevel.M, QrOutputFormat.png, "application/json", True),
        ("Test with high error correction", QrErrorCorrectLevel.H, QrOutputFormat.png, "application/json", True),
        ("SVG Output Test", QrErrorCorrectLevel.L, QrOutputFormat.svg, "image/svg+xml", False),
        ("Another SVG", QrErrorCorrectLevel.Q, QrOutputFormat.svg, "image/svg+xml", False),
        ("", QrErrorCorrectLevel.M, QrOutputFormat.png, "application/json", True),  # Empty text
        (
            "!@#$%^&*()_+=-`~[]{};':\",./<>?",
            QrErrorCorrectLevel.M,
            QrOutputFormat.png,
            "application/json",
            True,
        ),  # Special chars
    ],
)
@pytest.mark.asyncio
async def test_generate_qr_code_success(
    client: TestClient,
    text: str,
    error_correction: QrErrorCorrectLevel,
    output_format: QrOutputFormat,
    expected_content_type: str,
    check_base64: bool,
):
    """Test successful generation of QR codes in PNG (Base64) and SVG formats."""
    payload = QrCodeInput(text=text, error_correction=error_correction, output_format=output_format)
    response = client.post("/api/qrcode/generate", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == expected_content_type

    if output_format == QrOutputFormat.png:
        output = QrCodeOutput(**response.json())
        assert output.error is None
        assert output.output_format == QrOutputFormat.png
        assert isinstance(output.qr_code_data, str)
        if text:  # Only check if qr_code_data is non-empty if text was provided
            assert len(output.qr_code_data) > 0
            if check_base64:
                # Attempt to decode Base64 to validate format
                try:
                    base64.b64decode(output.qr_code_data)
                except Exception:
                    pytest.fail("QR code data is not valid Base64")
        else:
            # Check that we get non-empty base64 data even for empty input
            assert isinstance(output.qr_code_data, str)
            assert len(output.qr_code_data) > 0
            try:
                base64.b64decode(output.qr_code_data)
            except Exception:
                pytest.fail("QR code data for empty input is not valid Base64")
    else:  # svg
        svg_content = response.text
        # Check for svg tag presence, allowing for XML declaration
        assert "<svg" in svg_content.lower()


# --- Test WiFi QR Code Generation ---


@pytest.mark.parametrize(
    "ssid, password, auth_type, hidden, error_correction, output_format, expected_content_type, expected_wifi_substrings",
    [
        # WPA/WPA2
        (
            "MyWiFi",
            "password123",
            WifiAuthType.WPA,
            False,
            QrErrorCorrectLevel.M,
            QrOutputFormat.png,
            "application/json",
            ["WIFI:T:WPA;S:MyWiFi;P:password123;H:false;;"],
        ),
        (
            "Another Net",
            'complex"P@ss;',
            WifiAuthType.WPA,
            True,
            QrErrorCorrectLevel.H,
            QrOutputFormat.svg,
            "image/svg+xml",
            ['WIFI:T:WPA;S:Another Net;P:complex\\"P@ss\\;;H:true;;'],
        ),  # Escaped chars
        # WEP
        (
            "WEPNet",
            "abcde",
            WifiAuthType.WEP,
            False,
            QrErrorCorrectLevel.L,
            QrOutputFormat.png,
            "application/json",
            ["WIFI:T:WEP;S:WEPNet;P:abcde;H:false;;"],
        ),
        # No Password
        (
            "OpenNet",
            None,
            WifiAuthType.NOPASS,
            False,
            QrErrorCorrectLevel.Q,
            QrOutputFormat.svg,
            "image/svg+xml",
            ["WIFI:T:nopass;S:OpenNet;P:;H:false;;"],
        ),
        # Hidden network
        (
            "HiddenSSID",
            "hiddenpass",
            WifiAuthType.WPA,
            True,
            QrErrorCorrectLevel.M,
            QrOutputFormat.png,
            "application/json",
            ["WIFI:T:WPA;S:HiddenSSID;P:hiddenpass;H:true;;"],
        ),
    ],
)
@pytest.mark.asyncio
async def test_generate_wifi_qr_code_success(
    client: TestClient,
    ssid: str,
    password: str | None,
    auth_type: WifiAuthType,
    hidden: bool,
    error_correction: QrErrorCorrectLevel,
    output_format: QrOutputFormat,
    expected_content_type: str,
    expected_wifi_substrings: list[str],
):
    """Test successful generation of WiFi QR codes."""
    payload_dict = {
        "ssid": ssid,
        "password": password,
        "auth_type": auth_type,
        "hidden": hidden,
        "error_correction": error_correction,
        "output_format": output_format,
    }
    payload_data = {k: v for k, v in payload_dict.items() if v is not None}
    payload = WifiQrCodeInput(**payload_data)

    response = client.post("/api/qrcode/generate-wifi", json=payload.model_dump(exclude_unset=True))

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == expected_content_type

    # Basic checks similar to regular QR code
    if output_format == QrOutputFormat.png:
        output = QrCodeOutput(**response.json())
        assert output.error is None
        assert output.output_format == QrOutputFormat.png
        assert isinstance(output.qr_code_data, str)
        assert len(output.qr_code_data) > 0
        try:
            base64.b64decode(output.qr_code_data)
        except Exception:
            pytest.fail("WiFi QR code data is not valid Base64")
    else:  # svg
        svg_content = response.text
        # Check for svg tag presence, allowing for XML declaration
        assert "<svg" in svg_content.lower()

    # Additionally, check if expected WiFi substrings are present in the generated data
    # This requires decoding the QR code regardless of format
    # (Implementation omitted for brevity, but would involve a QR decoding library)


@pytest.mark.parametrize(
    "ssid, password, auth_type, hidden, error_substring",
    [
        ("MyWiFi", None, WifiAuthType.WPA, False, "Password is required for WPA and WEP"),  # Missing password for WPA
        ("WEPNet", None, WifiAuthType.WEP, False, "Password is required for WPA and WEP"),  # Missing password for WEP
    ],
)
@pytest.mark.asyncio
async def test_generate_wifi_qr_code_missing_password(
    client: TestClient, ssid: str, password: str | None, auth_type: WifiAuthType, hidden: bool, error_substring: str
):
    """Test WiFi QR code generation failure when password is required but missing."""
    payload = WifiQrCodeInput(
        ssid=ssid,
        password=password,
        auth_type=auth_type,
        hidden=hidden,
        output_format=QrOutputFormat.png,  # Format doesn't matter for this error
        error_correction=QrErrorCorrectLevel.M,  # Add default error correction
    )
    response = client.post("/api/qrcode/generate-wifi", json=payload.model_dump(exclude_unset=True))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert error_substring in response.json()["detail"]
