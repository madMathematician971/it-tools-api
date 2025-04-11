from typing import Union

from pydantic import BaseModel, Field


class ChmodPermission(BaseModel):
    read: bool = False
    write: bool = False
    execute: bool = False


class ChmodNumericInput(BaseModel):
    owner: ChmodPermission = Field(default_factory=ChmodPermission)
    group: ChmodPermission = Field(default_factory=ChmodPermission)
    others: ChmodPermission = Field(default_factory=ChmodPermission)


class ChmodNumericOutput(BaseModel):
    numeric: str  # Return as string e.g., "755"


class ChmodSymbolicInput(BaseModel):
    numeric: Union[str, int]  # Accept string or int


class ChmodSymbolicOutput(BaseModel):
    symbolic: str  # Return as string e.g., "rwxr-xr-x"
