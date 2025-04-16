"""
MCP Tool for converting data between JSON, YAML, TOML, and XML formats.
"""

import json
import logging
from enum import Enum
from typing import Any

import toml
import xmltodict
import yaml

from mcp_server import mcp_app

logger = logging.getLogger(__name__)


class DataType(str, Enum):
    json = "json"
    yaml = "yaml"
    toml = "toml"
    xml = "xml"


@mcp_app.tool()
def convert_data(input_string: str, input_type: str, output_type: str) -> dict[str, str | None]:
    """
    Convert data between JSON, YAML, TOML, and XML formats.

    Args:
        input_string: The data string to convert.
        input_type: The format of the input string ('json', 'yaml', 'toml', 'xml').
        output_type: The desired output format ('json', 'yaml', 'toml', 'xml').

    Returns:
        A dictionary containing:
            output_string: The converted data string, or None if conversion failed.
            error: An error message string if conversion failed, otherwise None.
    """
    try:
        in_type = DataType(input_type.lower())
        out_type = DataType(output_type.lower())
    except ValueError:
        return {
            "output_string": None,
            "error": f"Invalid input or output type specified. Use one of {list(DataType.__members__)}.",
        }

    if not input_string or not input_string.strip():
        return {"output_string": None, "error": "Input string cannot be empty."}

    if in_type == out_type:
        return {"output_string": input_string, "error": None}

    parsed_data: Any = None
    error_msg: str | None = None

    # 1. Parse Input
    try:
        if in_type == DataType.json:
            parsed_data = json.loads(input_string)
        elif in_type == DataType.yaml:
            parsed_data = yaml.safe_load(input_string)
        elif in_type == DataType.toml:
            parsed_data = toml.loads(input_string)
        elif in_type == DataType.xml:
            parsed_data = xmltodict.parse(input_string, attr_prefix="", cdata_key="text")
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON input: {e}"
    except yaml.YAMLError as e:
        error_msg = f"Invalid YAML input: {e}"
    except toml.TomlDecodeError as e:
        error_msg = f"Invalid TOML input: {e}"
    except xmltodict.expat.ExpatError as e:
        error_msg = f"Invalid XML input: {e}"
    except Exception as e:
        error_msg = f"Error parsing {in_type.value}: {e}"

    if error_msg:
        logger.warning(error_msg)
        return {"output_string": None, "error": error_msg}

    # 2. Prepare Data for Dumping (Handle XML input structure)
    data_to_dump = parsed_data
    if in_type == DataType.xml:
        # Extract data from the root element if it exists and is the only key
        if isinstance(parsed_data, dict) and len(parsed_data) == 1:
            inner_data = list(parsed_data.values())[0]
            # Also check for the specific list structure xmltodict might create
            if isinstance(inner_data, dict) and len(inner_data) == 1 and list(inner_data.keys())[0] == "item":
                item_content = inner_data["item"]
                # Ensure it's a list even if XML only had one item
                data_to_dump = item_content if isinstance(item_content, list) else [item_content]
            else:
                data_to_dump = inner_data
        # If not a single-root dict, pass original parsed data (might be error or unusual XML)

    # 3. Dump Output
    output_string: str | None = None
    error_msg = None  # Reset error message for dumping phase
    try:
        if out_type == DataType.json:
            output_string = json.dumps(data_to_dump, indent=2)
        elif out_type == DataType.yaml:
            output_string = yaml.dump(data_to_dump, allow_unicode=True, default_flow_style=False)
        elif out_type == DataType.toml:
            # TOML requires a dictionary at the top level
            if not isinstance(data_to_dump, dict):
                raise ValueError("TOML output requires a dictionary structure.")
            output_string = toml.dumps(data_to_dump)
        elif out_type == DataType.xml:
            # xmltodict needs a root element. Handle lists and non-dicts explicitly.
            root_data: Any
            if isinstance(data_to_dump, list):
                root_data = {"root": {"item": data_to_dump}}
            elif isinstance(data_to_dump, dict):
                if len(data_to_dump) == 1:
                    root_data = data_to_dump
                else:
                    root_data = {"root": data_to_dump}
            else:
                # Wrap scalars
                root_data = {"root": data_to_dump}
            output_string = xmltodict.unparse(root_data, pretty=True)

        logger.info(f"Successfully converted data from {in_type.value} to {out_type.value}")
        return {"output_string": output_string, "error": None}

    except ValueError as e:  # Catch specific errors like TOML needing dict
        error_msg = f"Error converting data to {out_type.value}: {e}"
    except Exception as e:
        error_msg = f"Error converting data to {out_type.value}: {e}"

    if error_msg:
        logger.error(f"{error_msg} (Input type: {in_type.value})", exc_info=True)
        return {"output_string": None, "error": error_msg}

    return {"output_string": None, "error": "Unknown error during data conversion."}
