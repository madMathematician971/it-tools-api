"""MCP Tools for converting between JSON and CSV formats."""

import csv
import io
import json
import logging
from typing import Any

from mcp_server import mcp_app

logger = logging.getLogger(__name__)


@mcp_app.tool()
def json_to_csv(json_string: str, delimiter: str = ",") -> dict[str, Any]:
    """
    Convert a JSON string (representing a list of objects) to CSV format.

    Args:
        json_string: The JSON string to convert. Must be an array/list of objects.
        delimiter: The delimiter character to use in the CSV output (default: ',').

    Returns:
        A dictionary containing:
            result_csv: The resulting data in CSV format (string).
            error: Error message if conversion failed.
    """
    try:
        # Parse JSON
        try:
            json_data = json.loads(json_string)
        except json.JSONDecodeError as e:
            return {"result_csv": "", "error": f"Invalid JSON input: {e}"}

        if isinstance(json_data, dict):
            json_data = [json_data]  # Handle single object case

        if not isinstance(json_data, list):
            return {"result_csv": "", "error": "Input JSON must be an array/list of objects or a single object."}
        if not json_data:
            return {"result_csv": "", "error": "Input JSON array cannot be empty."}

        # Get fieldnames from the first object if possible, then update with others
        fieldnames = set()
        for item in json_data:
            if not isinstance(item, dict):
                return {"result_csv": "", "error": "Each item in the JSON array must be an object."}
            fieldnames.update(item.keys())

        if not fieldnames:
            return {"result_csv": "", "error": "Could not determine headers from JSON objects."}

        fieldnames_list = sorted(list(fieldnames))

        # Write CSV to string
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames_list, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(json_data)

        return {"result_csv": output.getvalue(), "error": None}

    except Exception as e:
        logger.error(f"Error converting JSON to CSV: {e}", exc_info=True)
        return {"result_csv": "", "error": f"Internal server error during JSON to CSV conversion: {str(e)}"}


@mcp_app.tool()
def csv_to_json(csv_string: str, delimiter: str = ",") -> dict[str, Any]:
    """
    Convert CSV data (string) to a JSON string representation of a list of objects.

    Args:
        csv_string: The CSV data as a string.
        delimiter: The delimiter character used in the CSV input (default: ',').

    Returns:
        A dictionary containing:
            result_json: The resulting data as a JSON string.
            error: Error message if conversion failed.
    """
    try:
        csv_data = csv_string.strip()
        if not csv_data:
            return {"result_json": "[]", "error": None}

        csv_file = io.StringIO(csv_data)
        reader = csv.DictReader(csv_file, delimiter=delimiter)
        original_fieldnames = reader.fieldnames

        # Check for empty file after stripping header
        if not original_fieldnames:
            # If header was present but file only contained header or whitespace,
            # DictReader might parse fieldnames but list(reader) will be empty.
            # Check if only one line (header) existed in original stripped data.
            if len(csv_data.splitlines()) <= 1:
                return {"result_json": "[]", "error": None}
            else:
                # This case is less likely if DictReader got fieldnames, but defensive
                return {"result_json": "", "error": "CSV header found but no data rows could be parsed."}

        # Attempt to read all rows. Exceptions will be caught below.
        result_list = list(reader)

        # Process results: Strip keys and values
        cleaned_fieldnames = [field.strip() for field in original_fieldnames]
        final_data = []
        for row_dict in result_list:
            new_row = {}
            for i, cleaned_key in enumerate(cleaned_fieldnames):
                original_key = original_fieldnames[i]
                value = row_dict.get(original_key)
                if isinstance(value, str):
                    value = value.strip()
                new_row[cleaned_key] = value
            final_data.append(new_row)

        json_result_str = json.dumps(final_data, indent=2)
        return {"result_json": json_result_str, "error": None}

    except Exception as e:
        # Catch ALL errors during CSV processing (including csv.Error, sniffing issues, etc.)
        logger.warning(f"CSV to JSON conversion failed: {e}")
        # Return a generic error message
        return {"result_json": "", "error": f"Failed to process CSV: {str(e)}"}
