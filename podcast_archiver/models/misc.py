from __future__ import annotations

from pydantic import BaseModel, Field

from podcast_archiver.models.field_types import LenientInt


class Link(BaseModel):
    rel: str = ""
    link_type: str = Field("", alias="type")
    href: str
    length: LenientInt = None
