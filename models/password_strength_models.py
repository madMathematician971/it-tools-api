from typing import List, Optional

from pydantic import BaseModel


class PasswordInput(BaseModel):
    password: str


class CrackTimeSeconds(BaseModel):
    offline_fast_hashing_1e10_per_second: float
    offline_slow_hashing_1e4_per_second: float
    online_no_throttling_10_per_second: float
    online_throttling_100_per_hour: float


class CrackTimeDisplay(BaseModel):
    offline_fast_hashing_1e10_per_second: str
    offline_slow_hashing_1e4_per_second: str
    online_no_throttling_10_per_second: str
    online_throttling_100_per_hour: str


class Feedback(BaseModel):
    warning: Optional[str] = None
    suggestions: List[str] = []


class SequenceItem(BaseModel):
    pattern: str
    pattern_name: str
    token: str
    token_start_index: int
    token_end_index: int
    i: int
    j: int
    sub_display: str
    base_entropy_per_char: float
    entropy_per_char: float
    repeat_count: int
    base_token: str
    token_entropy: float
    match_entropy: float


class PasswordStrengthOutput(BaseModel):
    password: str
    entropy: float
    crack_time_seconds: CrackTimeSeconds
    crack_time_display: CrackTimeDisplay
    score: int
    feedback: Feedback
    calc_time: int
    matches: List[SequenceItem] = []
    strength: str
    error: Optional[str] = None
