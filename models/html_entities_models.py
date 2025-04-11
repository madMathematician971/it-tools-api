from pydantic import BaseModel


class HtmlEntitiesInput(BaseModel):
    text: str


class HtmlEntitiesOutput(BaseModel):
    result: str
