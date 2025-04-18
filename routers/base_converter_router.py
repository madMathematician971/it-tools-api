import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.base_converter import base_convert as base_convert_tool
from models.base_converter_models import BaseConvertInput, BaseConvertOutput

router = APIRouter(prefix="/api/base", tags=["Base Converter"])
logger = logging.getLogger(__name__)


@router.post("/convert", response_model=BaseConvertOutput)
async def base_convert_endpoint(payload: BaseConvertInput):
    """Convert an integer between different bases (2-36)."""
    try:
        result_dict = base_convert_tool(**payload.model_dump())
        if result_dict.get("error"):
            logger.info(f"Base conversion failed: {result_dict['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result_dict["error"],
            )

        return result_dict

    except ValueError as e:
        logger.info(f"Base conversion ValueError: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting base: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during base conversion",
        )
