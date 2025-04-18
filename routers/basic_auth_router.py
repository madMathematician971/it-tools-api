import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.basic_auth_generator import generate_basic_auth_header as generate_basic_auth_tool
from models.basic_auth_models import BasicAuthInput, BasicAuthOutput

router = APIRouter(prefix="/api/basic-auth", tags=["Basic Auth"])
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=BasicAuthOutput)
async def basic_auth_generate_endpoint(payload: BasicAuthInput):
    """Generate Basic Authentication header value."""
    try:
        result_dict = generate_basic_auth_tool(username=payload.username, password=payload.password)

        if result_dict.get("error"):
            logger.error(f"Tool error generating Basic Auth: {result_dict['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal error: {result_dict['error']}",
            )

        return result_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Basic Auth: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error generating Basic Auth",
        )
