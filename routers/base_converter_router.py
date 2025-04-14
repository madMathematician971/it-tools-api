from fastapi import APIRouter, HTTPException, status

from models.base_converter_models import BaseConvertInput, BaseConvertOutput
from mcp_server.tools.base_converter import base_convert

router = APIRouter(prefix="/api/base", tags=["Base Converter"])


@router.post("/convert", response_model=BaseConvertOutput)
async def base_convert_(payload: BaseConvertInput):
    """Convert an integer between different bases (2-36)."""
    try:
        return base_convert(**payload.model_dump())
    except ValueError as e:
        # Pass through the error message directly
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid input: {e}")
    except Exception as e:
        print(f"Error converting base: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during base conversion",
        )
