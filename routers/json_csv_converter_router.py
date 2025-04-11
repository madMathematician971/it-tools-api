import csv
import io
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status

from models.json_csv_converter_models import JsonCsvInput, JsonCsvOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/json-csv-converter", tags=["JSON CSV Converter"])


@router.post("/", response_model=JsonCsvOutput)
async def convert_data(input_data: JsonCsvInput):
    """Convert between JSON and CSV formats. Automatically detects the input format."""
    try:
        data = input_data.data.strip()
        if not data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input data cannot be empty")

        # Detect input format
        try:
            # First try to parse as JSON
            parsed_json = json.loads(data)
            # If successful, convert JSON to CSV
            return convert_json_to_csv(parsed_json, input_data.delimiter)
        except json.JSONDecodeError:
            # If not valid JSON, try to parse as CSV
            return convert_csv_to_json(data, input_data.delimiter)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error converting data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to convert data: {str(e)}"
        )


def convert_json_to_csv(json_data: Any, delimiter: str) -> JsonCsvOutput:
    """Convert JSON data to CSV format."""
    if isinstance(json_data, dict):
        # Single object - transform to list
        json_data = [json_data]

    if not isinstance(json_data, list) or not json_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Input JSON must be an array/list of objects"
        )

    # Get all unique keys
    fieldnames = set()
    for item in json_data:
        if isinstance(item, dict):
            fieldnames.update(item.keys())
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Each item in the JSON array must be an object"
            )

    # Sort fieldnames for consistency
    fieldnames = sorted(fieldnames)

    # Write CSV to string
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=delimiter)
    writer.writeheader()
    writer.writerows(json_data)

    return JsonCsvOutput(result=output.getvalue(), format="CSV")


def convert_csv_to_json(csv_data: str, delimiter: str) -> JsonCsvOutput:
    """Convert CSV data to JSON format."""
    # Parse CSV
    try:
        # Force iteration within the try block to catch parsing errors
        csv_file = io.StringIO(csv_data)
        reader = csv.DictReader(csv_file, delimiter=delimiter)
        # Check for empty file after potential header
        if not reader.fieldnames:
            # Handle empty input or header-only CSV
            if not csv_data.strip():  # Truly empty
                raise csv.Error("Empty CSV input")
            # Only headers present or malformed line preventing fieldname detection
            # Attempt basic line check
            sniffer = csv.Sniffer()
            try:
                sniffer.sniff(csv_data, delimiters=delimiter)
            except csv.Error as sniff_err:
                raise csv.Error(f"Malformed CSV or invalid delimiter: {sniff_err}") from sniff_err
            # Likely header only or just spaces
            return JsonCsvOutput(result="[]", format="JSON")

        # Attempt to read all rows to trigger potential errors
        result = list(reader)  # This will raise csv.Error if structure is bad

        if not result:
            return JsonCsvOutput(result="[]", format="JSON")

        # Convert to JSON
        json_result = json.dumps(result, indent=2)
        return JsonCsvOutput(result=json_result, format="JSON")
    except csv.Error as e:
        # Catch specific CSV errors during reading or sniffing
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid CSV format: {str(e)}")
    except Exception as e:
        # Catch other unexpected errors during CSV processing
        logger.error(f"Unexpected error processing CSV: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing CSV data: {str(e)}"
        )
