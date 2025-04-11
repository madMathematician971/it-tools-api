from enum import Enum

from pydantic import BaseModel, Field


class LoremType(str, Enum):
    words = "words"
    sentences = "sentences"
    paragraphs = "paragraphs"


class LoremInput(BaseModel):
    count: int = Field(5, gt=0, description="Number of words/sentences/paragraphs to generate")
    lorem_type: LoremType = Field(LoremType.paragraphs, description="Type of text to generate")


class LoremOutput(BaseModel):
    text: str
