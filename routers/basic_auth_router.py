import base64

from fastapi import APIRouter, HTTPException, status

from models.basic_auth_models import BasicAuthInput, BasicAuthOutput

router = APIRouter(prefix="/api/basic-auth", tags=["Basic Auth"])


@router.post("/generate", response_model=BasicAuthOutput)
async def basic_auth_generate(payload: BasicAuthInput):
    """Generate Basic Authentication header value."""
    try:
        credentials = f"{payload.username}:{payload.password}"
        encoded_credentials_bytes = base64.b64encode(credentials.encode("utf-8"))
        encoded_credentials_str = encoded_credentials_bytes.decode("utf-8")
        header_value = f"Basic {encoded_credentials_str}"
        return {
            "username": payload.username,
            "password": payload.password,
            "base64": encoded_credentials_str,
            "header": header_value,
        }
    except Exception as e:
        print(f"Error generating Basic Auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error generating Basic Auth",
        )
