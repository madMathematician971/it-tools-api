from pydantic import BaseModel


class MarkdownInput(BaseModel):
    markdown_string: str


class HtmlOutput(BaseModel):
    html_string: str
