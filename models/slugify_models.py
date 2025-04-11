from pydantic import BaseModel


class SlugifyInput(BaseModel):
    text: str


class SlugifyOutput(BaseModel):
    slug: str
