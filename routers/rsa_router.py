from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import APIRouter, HTTPException, status

from models.rsa_models import RsaKeygenInput, RsaKeygenOutput

router = APIRouter(prefix="/api/rsa", tags=["RSA"])

PUBLIC_EXPONENT = 65537


@router.post("/generate-keys", response_model=RsaKeygenOutput)
async def generate_rsa_keys(payload: RsaKeygenInput):
    """Generate an RSA public/private key pair in PEM format."""
    try:
        private_key = rsa.generate_private_key(
            public_exponent=PUBLIC_EXPONENT,
            key_size=payload.key_size,
            backend=default_backend(),
        )
        public_key = private_key.public_key()

        # Serialize private key to PEM (PKCS8 format, unencrypted)
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        # Serialize public key to PEM (SubjectPublicKeyInfo format)
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        return {
            "private_key_pem": private_pem,
            "public_key_pem": public_pem,
            "key_size": payload.key_size,
        }
    except Exception as e:
        print(f"Error generating RSA keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during RSA key generation",
        )
