import logging

from fastapi import APIRouter, HTTPException, status

# Import the MCP tool
from mcp_server.tools.datetime_parser import parse_datetime as parse_datetime_tool
from models.datetime_models import DateTimeConvertInput, DateTimeConvertOutput

router = APIRouter(prefix="/api/datetime", tags=["DateTime"])
logger = logging.getLogger(__name__)


@router.post("/convert", response_model=DateTimeConvertOutput)
async def datetime_convert_endpoint(payload: DateTimeConvertInput):
    """Convert between various date/time formats and timestamps using the MCP tool."""

    # Call the MCP tool
    result = parse_datetime_tool(
        input_value=payload.input_value,
        input_format=payload.input_format,
        output_format=payload.output_format,
    )

    # Check for errors from the tool
    if result.get("error"):
        error_detail = result["error"]
        logger.warning(f"Datetime tool returned error: {error_detail}")
        # Tool handles input/format validation, treat as 400
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)

    # Check if the result is present (should be if no error)
    if result.get("result") is not None:
        # The tool result dict contains the necessary fields for the output model
        return DateTimeConvertOutput(
            result=result["result"],
            input_value=payload.input_value,  # Include original input in response
            input_format=payload.input_format,  # Include original format in response
            output_format=payload.output_format,  # Include original output format
            parsed_utc_iso=result["parsed_utc_iso"],
        )
    else:
        # Handle unexpected case where result is None but error is also None
        logger.error("Datetime tool returned no result and no error.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error: Datetime tool returned unexpected state.",
        )
