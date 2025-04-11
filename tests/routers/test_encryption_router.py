import base64

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.encryption_models import CryptoDecryptInput, CryptoDecryptOutput, CryptoEncryptOutput, CryptoInput
from routers.encryption_router import router as encryption_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(encryption_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Encryption and Decryption --- A full cycle


@pytest.mark.parametrize(
    "text, password, algorithm",
    [
        ("This is a secret message.", "correctpassword", "aes-256-cbc"),
        ("Another secret!", "anotherPa$$w0rd", "aes-256-cbc"),
        ("", "emptypass", "aes-256-cbc"),  # Empty text
        ("Text with special chars !@#$%^&*()_+<>?:", "specialpass", "aes-256-cbc"),
    ],
)
@pytest.mark.asyncio
async def test_encrypt_decrypt_cycle(client: TestClient, text: str, password: str, algorithm: str):
    """Test encrypting and then decrypting successfully."""
    # 1. Encrypt
    encrypt_payload = CryptoInput(text=text, password=password, algorithm=algorithm)
    encrypt_response = client.post("/api/crypto/encrypt", json=encrypt_payload.model_dump())

    assert encrypt_response.status_code == status.HTTP_200_OK
    encrypt_output = CryptoEncryptOutput(**encrypt_response.json())
    ciphertext = encrypt_output.ciphertext
    assert isinstance(ciphertext, str)
    assert len(ciphertext) > 20  # Basic check that ciphertext is not empty

    # Verify it's base64 decodable
    try:
        base64.b64decode(ciphertext)
    except Exception:
        pytest.fail("Encrypted output is not valid Base64")

    # 2. Decrypt
    decrypt_payload = CryptoDecryptInput(ciphertext=ciphertext, password=password, algorithm=algorithm)
    decrypt_response = client.post("/api/crypto/decrypt", json=decrypt_payload.model_dump())

    assert decrypt_response.status_code == status.HTTP_200_OK
    decrypt_output = CryptoDecryptOutput(**decrypt_response.json())
    assert decrypt_output.plaintext == text


# --- Test Decryption Failures ---


@pytest.mark.asyncio
async def test_decrypt_wrong_password(client: TestClient):
    """Test decryption failure with the wrong password."""
    text = "secret data"
    correct_password = "rightpassword"
    wrong_password = "wrongpassword"
    algorithm = "aes-256-cbc"

    # Encrypt with correct password
    encrypt_payload = CryptoInput(text=text, password=correct_password, algorithm=algorithm)
    encrypt_response = client.post("/api/crypto/encrypt", json=encrypt_payload.model_dump())
    assert encrypt_response.status_code == status.HTTP_200_OK
    ciphertext = CryptoEncryptOutput(**encrypt_response.json()).ciphertext

    # Attempt to decrypt with wrong password
    decrypt_payload = CryptoDecryptInput(ciphertext=ciphertext, password=wrong_password, algorithm=algorithm)
    decrypt_response = client.post("/api/crypto/decrypt", json=decrypt_payload.model_dump())

    assert decrypt_response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Decryption failed" in decrypt_response.json()["detail"]  # Expecting padding error or similar


@pytest.mark.parametrize(
    "corrupted_ciphertext_modifier",
    [
        lambda c: c[:-5] + "xxxxx",  # Modify end
        lambda c: "A" + c[1:],  # Modify start (might affect salt/iv)
        lambda c: c[: len(c) // 2] + "B" + c[len(c) // 2 + 1 :],  # Modify middle
        lambda c: c + "extra",  # Append data
        lambda c: c[:-10],  # Truncate data (might be too short)
        lambda c: "invalid base64 !!!",  # Completely invalid base64
    ],
)
@pytest.mark.asyncio
async def test_decrypt_corrupted_data(client: TestClient, corrupted_ciphertext_modifier):
    """Test decryption failure with corrupted/modified ciphertext."""
    text = "original data"
    password = "password123"
    algorithm = "aes-256-cbc"

    # Encrypt first
    encrypt_payload = CryptoInput(text=text, password=password, algorithm=algorithm)
    encrypt_response = client.post("/api/crypto/encrypt", json=encrypt_payload.model_dump())
    assert encrypt_response.status_code == status.HTTP_200_OK
    original_ciphertext = CryptoEncryptOutput(**encrypt_response.json()).ciphertext

    # Corrupt the ciphertext
    corrupted_ciphertext = corrupted_ciphertext_modifier(original_ciphertext)

    # Attempt to decrypt
    decrypt_payload = CryptoDecryptInput(ciphertext=corrupted_ciphertext, password=password, algorithm=algorithm)
    decrypt_response = client.post("/api/crypto/decrypt", json=decrypt_payload.model_dump())

    # Expect either 400 (decryption failed) or 200 (decryption succeeded but produced garbage)
    if decrypt_response.status_code == status.HTTP_200_OK:
        output = CryptoDecryptOutput(**decrypt_response.json())
        assert output.plaintext != text, "Decryption succeeded but yielded original text despite corruption."
    elif decrypt_response.status_code == status.HTTP_400_BAD_REQUEST:
        # This is the ideal case, decryption failed as expected.
        pass
    else:
        pytest.fail(f"Unexpected status code {decrypt_response.status_code} for corrupted data decryption.")


# --- Test Algorithm Validation ---


@pytest.mark.parametrize("endpoint", ["encrypt", "decrypt"])
@pytest.mark.asyncio
async def test_invalid_algorithm(client: TestClient, endpoint: str):
    """Test using an unsupported algorithm."""
    payload_data = {
        "password": "pw",
        "algorithm": "des",  # Unsupported
        "text": "data" if endpoint == "encrypt" else None,
        "ciphertext": "dummyciphertext" if endpoint == "decrypt" else None,
    }
    # Remove None values
    payload_dict = {k: v for k, v in payload_data.items() if v is not None}

    response = client.post(f"/api/crypto/{endpoint}", json=payload_dict)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported algorithm" in response.json()["detail"]
