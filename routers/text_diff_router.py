import difflib
import logging

from fastapi import APIRouter, HTTPException, status

from models.text_diff_models import DiffFormat, TextDiffInput, TextDiffOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/text-diff", tags=["Text Diff"])


@router.post("/", response_model=TextDiffOutput)
async def generate_text_diff(input_data: TextDiffInput):
    """Compare two texts and show the differences."""
    try:
        text1 = input_data.text1
        text2 = input_data.text2
        output_format = input_data.output_format

        # Optionally ignore whitespace
        if input_data.ignore_whitespace:
            lines1 = [line.strip() for line in text1.splitlines()]
            lines2 = [line.strip() for line in text2.splitlines()]
        else:
            lines1 = text1.splitlines()
            lines2 = text2.splitlines()

        # Generate diff based on format
        if output_format == DiffFormat.HTML:
            d = difflib.HtmlDiff(tabsize=4, wrapcolumn=80)
            diff = d.make_table(lines1, lines2, context=True, numlines=input_data.context_lines)
        elif output_format == DiffFormat.NDIFF:
            diff_lines = list(difflib.ndiff(lines1, lines2))
            diff = "\n".join(diff_lines)
        elif output_format == DiffFormat.UNIFIED:
            diff_lines = list(
                difflib.unified_diff(
                    lines1,
                    lines2,
                    fromfile="text1",
                    tofile="text2",
                    n=input_data.context_lines,
                )
            )
            diff = "\n".join(diff_lines)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid output format. Choose 'html', 'ndiff', or 'unified'",
            )

        return TextDiffOutput(diff=diff, format_used=output_format.value, error=None)

    except Exception as e:
        logger.error(f"Error generating text diff: {e}", exc_info=True)
        format_val_str = "unknown"
        if input_data and hasattr(input_data, "output_format") and isinstance(input_data.output_format, DiffFormat):
            format_val_str = input_data.output_format.value
        elif input_data and hasattr(input_data, "output_format"):
            format_val_str = str(input_data.output_format)

        return TextDiffOutput(diff="", format_used=format_val_str, error=f"Failed to generate diff: {str(e)}")
