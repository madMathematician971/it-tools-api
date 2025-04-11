import logging
import re
from enum import Enum
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/list-converter", tags=["List Converter"])


class ListFormat(str, Enum):
    COMMA_SEPARATED = "comma"
    NEWLINE_SEPARATED = "newline"
    SPACE_SEPARATED = "space"
    SEMICOLON_SEPARATED = "semicolon"
    BULLET_ASTERISK = "bullet_asterisk"  # * item
    BULLET_HYPHEN = "bullet_hyphen"  # - item
    NUMBERED_DOT = "numbered_dot"  # 1. item
    NUMBERED_PAREN = "numbered_paren"  # 1) item


class ListConverterInput(BaseModel):
    input_text: str = Field(..., description="The list text to convert.")
    input_format: ListFormat = Field(..., description="Format of the input list.")
    output_format: ListFormat = Field(..., description="Desired format for the output list.")
    ignore_empty: bool = Field(True, description="Ignore empty lines or items during conversion.")
    trim_items: bool = Field(True, description="Trim whitespace from each list item.")


class ListConverterOutput(BaseModel):
    result: str = Field(..., description="The list converted to the desired output format.")


# Helper to parse input based on format
def parse_list(text: str, input_format: ListFormat, ignore_empty: bool, trim_items: bool) -> List[str]:
    items = []
    if input_format == ListFormat.COMMA_SEPARATED:
        items = text.split(",")
    elif input_format == ListFormat.NEWLINE_SEPARATED:
        items = text.splitlines()
    elif input_format == ListFormat.SPACE_SEPARATED:
        items = text.split()
    elif input_format == ListFormat.SEMICOLON_SEPARATED:
        items = text.split(";")
    elif input_format in [
        ListFormat.BULLET_ASTERISK,
        ListFormat.BULLET_HYPHEN,
        ListFormat.NUMBERED_DOT,
        ListFormat.NUMBERED_PAREN,
    ]:
        lines = text.splitlines()
        for line in lines:
            cleaned_line = line.strip()
            if input_format == ListFormat.BULLET_ASTERISK and cleaned_line.startswith("*"):
                items.append(cleaned_line[1:].strip() if trim_items else cleaned_line[1:])
            elif input_format == ListFormat.BULLET_HYPHEN and cleaned_line.startswith("-"):
                items.append(cleaned_line[1:].strip() if trim_items else cleaned_line[1:])
            elif input_format == ListFormat.NUMBERED_DOT and re.match(r"^\d+\.\s*", cleaned_line):
                item_text = re.sub(r"^\d+\.\s*", "", cleaned_line)
                items.append(item_text.strip() if trim_items else item_text)
            elif input_format == ListFormat.NUMBERED_PAREN and re.match(r"^\d+\)\s*", cleaned_line):
                item_text = re.sub(r"^\d+\)\s*", "", cleaned_line)
                items.append(item_text.strip() if trim_items else item_text)
            elif not ignore_empty:
                # If it doesn't match the expected bullet/number format, treat as item if not ignoring empty
                items.append(line.strip() if trim_items else line)
    else:
        # Fallback or error? Defaulting to newline for unknown input format for now.
        logger.warning(f"Unknown input format '{input_format}', attempting newline split.")
        items = text.splitlines()

    if trim_items:
        items = [item.strip() for item in items]
    if ignore_empty:
        items = [item for item in items if item]

    return items


# Helper to format output based on format
def format_list(items: List[str], output_format: ListFormat) -> str:
    if not items:
        return ""

    if output_format == ListFormat.COMMA_SEPARATED:
        return ",".join(items)
    elif output_format == ListFormat.NEWLINE_SEPARATED:
        return "\n".join(items)
    elif output_format == ListFormat.SPACE_SEPARATED:
        return " ".join(items)
    elif output_format == ListFormat.SEMICOLON_SEPARATED:
        return ";".join(items)
    elif output_format == ListFormat.BULLET_ASTERISK:
        return "\n".join([f"* {item}" for item in items])
    elif output_format == ListFormat.BULLET_HYPHEN:
        return "\n".join([f"- {item}" for item in items])
    elif output_format == ListFormat.NUMBERED_DOT:
        return "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])
    elif output_format == ListFormat.NUMBERED_PAREN:
        return "\n".join([f"{i+1}) {item}" for i, item in enumerate(items)])
    else:
        logger.error(f"Unknown output format requested: {output_format}")
        raise ValueError(f"Unsupported output format: {output_format}")


@router.post(
    "/convert",
    response_model=ListConverterOutput,
    summary="Convert text between different list formats",
)
async def convert_list(payload: ListConverterInput):
    """Converts list items from one text format (e.g., comma-separated) to another (e.g., bullet points)."""
    try:
        parsed_items = parse_list(
            payload.input_text,
            payload.input_format,
            payload.ignore_empty,
            payload.trim_items,
        )
        formatted_result = format_list(parsed_items, payload.output_format)
        return ListConverterOutput(result=formatted_result)

    except ValueError as ve:
        logger.info(f"Error converting list: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(
            f"Error converting list from {payload.input_format} to {payload.output_format}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during list conversion: {str(e)}",
        )
