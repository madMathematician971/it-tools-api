import json
from typing import Any

import toml
import xmltodict
import yaml
from fastapi import APIRouter, HTTPException, status

from models.data_converter_models import DataConverterInput, DataConverterOutput, DataType

router = APIRouter(prefix="/api/data", tags=["Data Converter"])


def parse_input(input_string: str, input_type: DataType) -> Any:
    """Parse input string based on its type."""
    try:
        if input_type == DataType.json:
            return json.loads(input_string)
        elif input_type == DataType.yaml:
            return yaml.safe_load(input_string)
        elif input_type == DataType.toml:
            return toml.loads(input_string)
        elif input_type == DataType.xml:
            # XML usually parses into an OrderedDict with a single root key
            return xmltodict.parse(input_string)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON input: {e}")
    except yaml.YAMLError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid YAML input: {e}")
    except toml.TomlDecodeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid TOML input: {e}")
    except xmltodict.expat.ExpatError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid XML input: {e}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing {input_type.value}: {e}",
        )


def dump_output(data: Any, output_type: DataType) -> str:
    """Dump Python object to string based on output type."""
    try:
        if output_type == DataType.json:
            return json.dumps(data, indent=2)
        elif output_type == DataType.yaml:
            return yaml.dump(data, allow_unicode=True, default_flow_style=False)
        elif output_type == DataType.toml:
            # TOML requires a dictionary at the top level
            if not isinstance(data, dict):
                raise ValueError("TOML output requires a dictionary structure.")
            return toml.dumps(data)
        elif output_type == DataType.xml:
            # xmltodict needs a root element. Wrap lists specifically.
            root_data = data
            if isinstance(data, list):
                root_data = {"root": {"item": data}}
            elif not isinstance(data, dict) or len(data) != 1:
                # Wrap non-dicts or dicts without a single root key
                root_data = {"root": data}
            return xmltodict.unparse(root_data, pretty=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error converting data to {output_type.value}: {e}",
        )


@router.post("/convert", response_model=DataConverterOutput)
async def convert_data_format(payload: DataConverterInput):
    """Convert data between JSON, YAML, TOML, and XML formats."""
    if payload.input_type == payload.output_type:
        return DataConverterOutput(output_string=payload.input_string)

    try:
        parsed_data = parse_input(payload.input_string, payload.input_type)

        # If input was XML, extract data from the root element before dumping
        data_to_dump = parsed_data
        if payload.input_type == DataType.xml:
            if isinstance(parsed_data, dict) and len(parsed_data) == 1:
                inner_data = list(parsed_data.values())[0]
                # Also check for the list structure we created
                if isinstance(inner_data, dict) and len(inner_data) == 1 and list(inner_data.keys())[0] == "item":
                    item_content = inner_data["item"]
                    data_to_dump = item_content if isinstance(item_content, list) else [item_content]
                else:
                    data_to_dump = inner_data
            # If not a single-root dict, pass original parsed data (might be error or unusual XML)

        output_string = dump_output(data_to_dump, payload.output_type)
        return DataConverterOutput(output_string=output_string)
    except HTTPException as e:
        # Re-raise HTTPExceptions raised by parse/dump functions
        raise e
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected error during data conversion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during data conversion",
        )
