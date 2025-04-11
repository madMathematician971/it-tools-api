from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RegexInput(BaseModel):
    regex_pattern: str = Field(..., description="Regular expression pattern")
    test_string: str = Field("", description="String to test the regex against")
    ignore_case: bool = Field(False, description="Perform case-insensitive matching")
    multiline: bool = Field(False, description="Make ^ and $ match start/end of lines")
    dot_all: bool = Field(False, description="Make . match newline characters")
    # global_match: bool = Field(True, description="Find all matches (currently always true)")


class RegexMatch(BaseModel):
    match_index: int  # Overall match index (0, 1, 2...)
    start: int
    end: int
    matched_string: str
    groups: List[str]  # Captured groups
    named_groups: Dict[str, str]  # Captured named groups


class RegexOutput(BaseModel):
    matches: List[RegexMatch]
    error: Optional[str] = None
