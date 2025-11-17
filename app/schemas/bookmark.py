"""Pydantic schemas for Bookmark API"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl

from app.models.bookmark import ContentType


class BookmarkCreate(BaseModel):
    """Schema for creating a new bookmark"""

    content_type: ContentType = Field(..., description="Type of content being bookmarked")
    url: Optional[str] = Field(None, description="URL for url/image/video/pdf content types")
    title: Optional[str] = Field(None, max_length=500, description="Optional title")
    description: Optional[str] = Field(None, max_length=2000, description="Optional description")
    raw_content: Optional[str] = Field(None, description="Raw text content (for text type)")
    platform_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Platform-specific metadata")

    monitoring_enabled: bool = Field(True, description="Enable monitoring for changes")
    check_interval: int = Field(60, ge=5, le=10080, description="Check interval in minutes (5 min to 7 days)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content_type": "url",
                    "url": "https://example.com/article",
                    "title": "Interesting Article",
                    "monitoring_enabled": True,
                    "check_interval": 60
                },
                {
                    "content_type": "text",
                    "title": "Important Note",
                    "raw_content": "Remember to check this later",
                    "monitoring_enabled": False
                }
            ]
        }
    }


class BookmarkUpdate(BaseModel):
    """Schema for updating a bookmark"""

    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    monitoring_enabled: Optional[bool] = None
    check_interval: Optional[int] = Field(None, ge=5, le=10080)
    platform_data: Optional[Dict[str, Any]] = None


class BookmarkResponse(BaseModel):
    """Schema for bookmark response"""

    id: str
    user_id: str
    content_type: ContentType
    url: Optional[str]
    title: Optional[str]
    description: Optional[str]
    raw_content: Optional[str]
    file_path: Optional[str]
    platform_data: Dict[str, Any]
    monitoring_enabled: bool
    check_interval: int
    created_at: datetime
    last_checked_at: Optional[datetime]

    model_config = {"from_attributes": True}


class BookmarkListResponse(BaseModel):
    """Schema for paginated bookmark list"""

    items: List[BookmarkResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
