from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LinkCreate(BaseModel):
    long_url: str = Field(..., description="The destination URL")
    short_code: Optional[str] = Field(None, min_length=3, max_length=16)
    expires_at: Optional[datetime] = None


class LinkUpdate(BaseModel):
    long_url: Optional[str] = None
    expires_at: Optional[datetime] = None


class LinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    short_code: str
    long_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    owner_id: Optional[int] = None


class TopLinkOut(BaseModel):
    short_code: str
    long_url: str
    click_count: int


class ClicksOverTimePoint(BaseModel):
    date: date
    count: int
