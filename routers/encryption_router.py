import base64
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fastapi import APIRouter, HTTPException, status

from models.encryption_models import (
    CryptoDecryptInput,
    CryptoDecryptOutput,
    CryptoEncryptOutput,
    CryptoInput,
)

router = APIRouter(prefix="/api/crypto", tags=["Encryption"])

# Constants
SALT_SIZE = 16
IV_SIZE = 16
KEY_SIZE = 32
ITERATIONS = 100000


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a key from password and salt using PBKDF2 HMAC SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend(),
    )
    return kdf.derive(password.encode("utf-8"))


@router.post("/encrypt", response_model=CryptoEncryptOutput)
async def crypto_encrypt(payload: CryptoInput):
    """Encrypt text using AES-256-CBC with PBKDF2 key derivation."""
    if payload.algorithm.lower() != "aes-256-cbc":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported algorithm. Only 'aes-256-cbc' is implemented.",
        )

    try:
        salt = os.urandom(SALT_SIZE)
        key = derive_key(payload.password, salt)
        iv = os.urandom(IV_SIZE)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(payload.text.encode("utf-8")) + padder.finalize()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        combined_data = salt + iv + encrypted_data
        ciphertext_b64 = base64.b64encode(combined_data).decode("utf-8")
        return {"ciphertext": ciphertext_b64}
    except Exception as e:
        print(f"Error encrypting data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during encryption",
        )


@router.post("/decrypt", response_model=CryptoDecryptOutput)
async def crypto_decrypt(payload: CryptoDecryptInput):
    """Decrypt text encrypted with the corresponding encrypt endpoint."""
    if payload.algorithm.lower() != "aes-256-cbc":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported algorithm. Only 'aes-256-cbc' is implemented.",
        )

    try:
        try:
            combined_data = base64.b64decode(payload.ciphertext)
        except base64.binascii.Error:
            raise ValueError("Invalid Base64 ciphertext.")

        if len(combined_data) < SALT_SIZE + IV_SIZE:
            raise ValueError("Ciphertext is too short to contain salt and IV.")

        salt = combined_data[:SALT_SIZE]
        iv = combined_data[SALT_SIZE : SALT_SIZE + IV_SIZE]
        encrypted_data = combined_data[SALT_SIZE + IV_SIZE :]
        key = derive_key(payload.password, salt)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(encrypted_data) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        return {"plaintext": plaintext.decode("utf-8")}
    except ValueError as e:
        print(f"Error decrypting data (likely bad password or corrupt data): {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Decryption failed: {e}")
    except Exception as e:
        print(f"Error decrypting data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during decryption",
        )
