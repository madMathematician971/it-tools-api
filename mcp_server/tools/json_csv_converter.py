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
