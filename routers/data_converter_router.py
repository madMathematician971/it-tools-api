import logging

from fastapi import APIRouter, HTTPException, status

# Import the MCP tool function
from mcp_server.tools.data_converter import convert_data as convert_data_tool
from models.data_converter_models import DataConverterInput, DataConverterOutput

router = APIRouter(prefix="/api/data", tags=["Data Converter"])
logger = logging.getLogger(__name__)


@router.post("/convert", response_model=DataConverterOutput)
async def convert_data_format(payload: DataConverterInput):
    """Convert data between JSON, YAML, TOML, and XML formats using the MCP tool."""

    # Call the MCP tool
    result = convert_data_tool(
        input_string=payload.input_string,
        input_type=payload.input_type.value,
        output_type=payload.output_type.value,
    )

    # Check the result from the tool
    if result["error"]:
        error_detail = result["error"]
        logger.warning(f"Data conversion tool returned error: {error_detail}")
        # Determine status code based on error type (heuristic)
        status_code = status.HTTP_400_BAD_REQUEST
        if "Error converting data to" in error_detail or "Unknown error" in error_detail:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        elif "Invalid input or output type" in error_detail or "Input string cannot be empty" in error_detail:
            status_code = status.HTTP_400_BAD_REQUEST
        elif "Invalid" in error_detail and ("input:" in error_detail or "XML input:" in error_detail):
            status_code = status.HTTP_400_BAD_REQUEST  # Specific parsing errors

        raise HTTPException(status_code=status_code, detail=error_detail)

    if result["output_string"] is not None:
        return DataConverterOutput(output_string=result["output_string"])
    else:
        # Should not happen if error is None, but handle as internal server error
        logger.error("Data conversion tool returned no output and no error.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during data conversion: Tool returned unexpected state.",
        )
