from typing import Any, Dict

from pydantic import BaseModel, Field


class TextStatsInput(BaseModel):
    text: str


class TextStatsOutput(BaseModel):
    stats: Dict[str, Any] = Field(..., description="Dictionary containing various text statistics")
    # Example keys: char_count, char_count_no_spaces, word_count, line_count, sentence_count, paragraph_count
