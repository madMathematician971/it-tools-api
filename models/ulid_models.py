from pydantic import BaseModel, Field


class UlidResponse(BaseModel):
    ulid: str = Field(..., description="Generated ULID string")
    timestamp: str = Field(..., description="Timestamp part of ULID (ISO 8601 UTC)")
    timestamp_ms: int = Field(..., description="Timestamp part as milliseconds since epoch")
    randomness: str = Field(..., description="Randomness part of ULID (as hex)")
