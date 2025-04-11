from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class UserAgentInput(BaseModel):
    user_agent: str = Field(..., description="User-Agent string to parse")


class UserAgentOutput(BaseModel):
    browser: Optional[Dict[str, str]] = None
    os: Optional[Dict[str, str]] = None
    device: Optional[Dict[str, Any]] = None
    raw_user_agent: str
