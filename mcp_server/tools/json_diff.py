"""
JSON diff tool for MCP server.
"""

import json
import logging

from deepdiff import DeepDiff
from deepdiff.model import PrettyOrderedSet

from mcp_server import mcp_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _convert_deepdiff_to_serializable(item):
    """Recursively convert DeepDiff internal types to JSON serializable types."""
    if isinstance(item, dict):
        return {k: _convert_deepdiff_to_serializable(v) for k, v in item.items()}
    if isinstance(item, (list, set, PrettyOrderedSet)):
        return [_convert_deepdiff_to_serializable(i) for i in item]
    # Add other non-serializable types here if needed
    return item


@mcp_app.tool()
def json_diff(json1: str, json2: str, ignore_order: bool = False, output_format: str = "delta") -> dict:
    """
    Compare two JSON objects and return their differences.

    Args:
        json1: First JSON string
        json2: Second JSON string
        ignore_order: Whether to ignore array order
        output_format: Output format (delta or simple)

    Returns:
        A dictionary containing:
            diff: Generated JSON diff
            format_used: Output format used
            error: Optional error message
    """
    # Validate output format first
    output_format = output_format.lower()
    if output_format not in ["delta", "simple"]:
        return {"diff": "", "format_used": output_format, "error": "Invalid output format. Choose 'delta' or 'simple'"}

    try:
        # Parse JSON strings
        try:
            json1_obj = json.loads(json1)
        except json.JSONDecodeError as e:
            return {"diff": "", "format_used": output_format, "error": f"Invalid JSON in first input: {str(e)}"}

        try:
            json2_obj = json.loads(json2)
        except json.JSONDecodeError as e:
            return {"diff": "", "format_used": output_format, "error": f"Invalid JSON in second input: {str(e)}"}

        # Calculate diff using DeepDiff
        diff = DeepDiff(
            json1_obj,
            json2_obj,
            ignore_order=ignore_order,
            ignore_string_case=False,  # Keep case sensitivity for strings
            ignore_numeric_type_changes=True,  # Treat 1 and 1.0 as same
            view="text",  # Basic text view for simple format
        )

        # Format output
        if output_format == "delta":
            # Convert to serializable dict before dumping
            serializable_diff = _convert_deepdiff_to_serializable(diff.to_dict())
            diff_output = json.dumps(serializable_diff, indent=2, ensure_ascii=False)
        else:  # output_format == "simple"
            # Basic text representation from DeepDiff
            diff_output = diff.pretty()

        return {"diff": diff_output, "format_used": output_format, "error": None}

    except Exception as e:
        logger.error(f"Error generating JSON diff: {e}", exc_info=True)
        return {"diff": "", "format_used": output_format, "error": f"Failed to generate diff: {str(e)}"}
