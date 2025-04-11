import json
import logging

from deepdiff import DeepDiff
from fastapi import APIRouter, HTTPException, status

from models.json_diff_models import JsonDiffInput, JsonDiffOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/json-diff", tags=["JSON Diff"])


@router.post("/", response_model=JsonDiffOutput)
async def generate_json_diff(input_data: JsonDiffInput):
    """Compare two JSON objects and show the differences."""

    # Validate output format first
    output_format = input_data.output_format.lower()
    if output_format not in ["delta", "simple"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid output format. Choose 'delta' or 'simple'"
        )

    try:
        # Parse JSON strings
        try:
            json1 = json.loads(input_data.json1)
        except json.JSONDecodeError as e:
            return JsonDiffOutput(
                diff="", format_used=input_data.output_format, error=f"Invalid JSON in first input: {str(e)}"
            )

        try:
            json2 = json.loads(input_data.json2)
        except json.JSONDecodeError as e:
            return JsonDiffOutput(
                diff="", format_used=input_data.output_format, error=f"Invalid JSON in second input: {str(e)}"
            )

        # Calculate diff using DeepDiff
        diff = DeepDiff(
            json1,
            json2,
            ignore_order=input_data.ignore_order,
            ignore_string_case=False,  # Keep case sensitivity for strings
            ignore_numeric_type_changes=True,  # Treat 1 and 1.0 as same
            view="text",  # Basic text view for simple format
        )

        # Format output (already validated)
        if output_format == "delta":
            # Use the detailed dictionary representation
            diff_output = json.dumps(diff.to_dict(), indent=2)
        else:  # output_format == "simple"
            # Basic text representation from DeepDiff
            diff_output = diff.pretty()

        return JsonDiffOutput(diff=diff_output, format_used=output_format)

    except Exception as e:
        logger.error(f"Error generating JSON diff: {e}", exc_info=True)
        return JsonDiffOutput(diff="", format_used=input_data.output_format, error=f"Failed to generate diff: {str(e)}")
