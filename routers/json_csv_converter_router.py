import json
import logging

from fastapi import APIRouter, HTTPException, status

# Import MCP tools
from mcp_server.tools.json_csv_converter import csv_to_json, json_to_csv
from models.json_csv_converter_models import JsonCsvInput, JsonCsvOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/json-csv-converter", tags=["JSON CSV Converter"])


@router.post("/", response_model=JsonCsvOutput)
async def convert_data_endpoint(payload: JsonCsvInput):
    """Convert between JSON and CSV formats using MCP tools, auto-detecting input."""
    try:
        data = payload.data.strip()
        if not data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input data cannot be empty")

        # Detect input format and call appropriate tool
        try:
            # First try to parse as JSON - if success, input is JSON, convert TO CSV
            json.loads(data)
            logger.info("Input detected as JSON, converting to CSV.")
            result = json_to_csv(json_string=data, delimiter=payload.delimiter)
            if result.get("error"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
            return JsonCsvOutput(result=result["result_csv"], format="CSV")

        except json.JSONDecodeError:
            # If not valid JSON, assume input is CSV, convert TO JSON
            logger.info("Input detected as CSV (not valid JSON), converting to JSON.")
            result = csv_to_json(csv_string=data, delimiter=payload.delimiter)
            if result.get("error"):
                # Use 400 for parsing errors, potentially 500 for unexpected internal tool errors?
                # Tool returns generic error, stick with 400 for now.
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
            return JsonCsvOutput(result=result["result_json"], format="JSON")

    except HTTPException:  # Re-raise HTTP exceptions raised within the try block
        raise
    except Exception as e:  # Catch unexpected errors *outside* the tool calls
        logger.error(f"Error in JSON/CSV conversion endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to convert data: {str(e)}"
        )
