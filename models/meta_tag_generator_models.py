from typing import Dict

from pydantic import BaseModel, Field


class MetaTagInput(BaseModel):
    title: str = Field(..., description="Title of the page")
    description: str = Field(..., description="Description of the page content")
    keywords: str = Field("", description="Comma-separated keywords")
    author: str = Field("", description="Author of the page")
    language: str = Field("en", description="Content language (ISO code)")
    robots: str = Field("index, follow", description="Robots directive")
    viewport: str = Field("width=device-width, initial-scale=1.0", description="Viewport settings")
    og_type: str = Field("website", description="OpenGraph type")
    og_url: str = Field("", description="OpenGraph URL")
    og_image: str = Field("", description="OpenGraph image URL")
    twitter_card: str = Field("summary", description="Twitter card type")
    twitter_site: str = Field("", description="Twitter site username")


class MetaTagOutput(BaseModel):
    html: str = Field(..., description="Generated HTML meta tags")
    tags: Dict[str, str] = Field(..., description="Dictionary of tags and values")
