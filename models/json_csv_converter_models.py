from pydantic import BaseModel, Field


class JsonCsvInput(BaseModel):
    data: str = Field(..., description="JSON data or CSV data to convert")
    delimiter: str = Field(",", description="Delimiter for CSV (comma by default)")


class JsonCsvOutput(BaseModel):
    result: str = Field(..., description="Converted data")
    format: str = Field(..., description="Format of the output data (JSON or CSV)")
