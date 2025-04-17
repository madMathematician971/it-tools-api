"""Tool for AES-256-CBC encryption and decryption using PBKDF2 key derivation."""

import base64
import logging
import os
from typing import Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from mcp_server import mcp_app

logger = logging.getLogger(__name__)

# Constants
SALT_SIZE = 16
IV_SIZE = 16
KEY_SIZE = 32
ITERATIONS = 100000


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a key from password and salt using PBKDF2 HMAC SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend(),
    )
    return kdf.derive(password.encode("utf-8"))


@mcp_app.tool()
def encrypt_text(text: str, password: str, algorithm: str) -> dict[str, Any]:
    """
    Encrypt text using a specified algorithm (currently only AES-256-CBC).

    Args:
        text: The plaintext string to encrypt.
        password: The password to use for key derivation.
        algorithm: The encryption algorithm (only 'aes-256-cbc' supported).

    Returns:
        A dictionary containing:
            ciphertext: The Base64 encoded ciphertext (salt + IV + encrypted data).
            error: An error message if encryption failed.
    """
    if algorithm.lower() != "aes-256-cbc":
        return {"ciphertext": None, "error": "Unsupported algorithm. Only 'aes-256-cbc' is implemented."}

    try:
        salt = os.urandom(SALT_SIZE)
        key = _derive_key(password, salt)
        iv = os.urandom(IV_SIZE)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()

        # Ensure text is encoded to bytes
        try:
            text_bytes = text.encode("utf-8")
        except UnicodeEncodeError as e:
            return {"ciphertext": None, "error": f"Input text contains characters that cannot be encoded to UTF-8: {e}"}

        padded_data = padder.update(text_bytes) + padder.finalize()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        combined_data = salt + iv + encrypted_data
        ciphertext_b64 = base64.b64encode(combined_data).decode("utf-8")
        return {"ciphertext": ciphertext_b64, "error": None}
    except Exception as e:
        logger.error(f"Error encrypting data: {e}", exc_info=True)
        return {"ciphertext": None, "error": f"Internal server error during encryption: {str(e)}"}


@mcp_app.tool()
def decrypt_text(ciphertext: str, password: str, algorithm: str) -> dict[str, Any]:
    """
    Decrypt text using a specified algorithm (currently only AES-256-CBC).

    Args:
        ciphertext: The Base64 encoded ciphertext (salt + IV + encrypted data).
        password: The password used for encryption.
        algorithm: The decryption algorithm (only 'aes-256-cbc' supported).

    Returns:
        A dictionary containing:
            plaintext: The decrypted plaintext string.
            error: An error message if decryption failed (e.g., bad password, corrupt data).
    """
    if algorithm.lower() != "aes-256-cbc":
        return {"plaintext": None, "error": "Unsupported algorithm. Only 'aes-256-cbc' is implemented."}

    try:
        try:
            combined_data = base64.b64decode(ciphertext)
        except base64.binascii.Error:
            # More specific error for bad base64
            return {"plaintext": None, "error": "Invalid Base64 ciphertext."}
        except Exception as e:
            logger.error(f"Error decoding base64 ciphertext: {e}", exc_info=True)
            return {"plaintext": None, "error": f"Error decoding Base64: {str(e)}"}

        if len(combined_data) < SALT_SIZE + IV_SIZE:
            return {"plaintext": None, "error": "Ciphertext is too short to contain salt and IV."}

        salt = combined_data[:SALT_SIZE]
        iv = combined_data[SALT_SIZE : SALT_SIZE + IV_SIZE]
        encrypted_data = combined_data[SALT_SIZE + IV_SIZE :]
        key = _derive_key(password, salt)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(encrypted_data) + decryptor.finalize()

        # Unpadding can fail if key/IV/data is incorrect
        try:
            unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
            plaintext_bytes = unpadder.update(padded_plaintext) + unpadder.finalize()
        except ValueError:
            # This is the most common error for wrong password/corrupt data
            return {"plaintext": None, "error": "Decryption failed. Likely incorrect password or corrupt/invalid data."}

        # Decoding the result can also fail
        try:
            plaintext = plaintext_bytes.decode("utf-8")
            return {"plaintext": plaintext, "error": None}
        except UnicodeDecodeError:
            return {"plaintext": None, "error": "Decryption succeeded but result is not valid UTF-8 text."}

    except Exception as e:
        logger.error(f"Unexpected error during decryption: {e}", exc_info=True)
        return {"plaintext": None, "error": f"Internal server error during decryption: {str(e)}"}
