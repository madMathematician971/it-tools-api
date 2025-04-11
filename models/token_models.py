from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class CharSetType(str, Enum):
    alphanumeric = "alphanumeric"  # a-z, A-Z, 0-9
    alpha = "alpha"  # a-z, A-Z
    numeric = "numeric"  # 0-9
    hex_lower = "hex_lower"  # 0-9, a-f
    hex_upper = "hex_upper"  # 0-9, A-F
    # Could add custom charset option


class TokenInput(BaseModel):
    length: int = Field(32, gt=0, description="Length of each token")
    count: int = Field(1, gt=0, le=100, description="Number of tokens to generate (max 100)")
    charset_type: CharSetType = Field(CharSetType.alphanumeric, description="Character set to use")


class TokenOutput(BaseModel):
    tokens: List[str]
