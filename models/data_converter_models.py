from enum import Enum
from typing import Optional

from pydantic import BaseModel


class DataType(str, Enum):
    json = "json"
    yaml = "yaml"
    toml = "toml"
    xml = "xml"


class DataConverterInput(BaseModel):
    input_string: str
    input_type: DataType
    output_type: DataType


class DataConverterOutput(BaseModel):
    output_string: str
    error: Optional[str] = None
