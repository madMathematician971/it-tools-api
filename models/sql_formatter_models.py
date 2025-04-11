from typing import Literal

from pydantic import BaseModel, Field

KeywordCase = Literal["upper", "lower", "capitalize"]


class SqlFormatInput(BaseModel):
    sql_string: str
    keyword_case: KeywordCase = Field("upper", description="Case for keywords (upper, lower, capitalize)")
    indent_width: int = Field(2, gt=0, description="Number of spaces for indentation")
    reindent: bool = Field(True, description="Re-indent statements")
    # Add other sqlparse options if needed


class SqlFormatOutput(BaseModel):
    formatted_sql: str
