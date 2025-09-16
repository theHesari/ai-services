from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid


class ContentType(str, Enum):
    BLOG_POST = "blog_post"
    SOCIAL_MEDIA = "social_media"
    EMAIL_NEWSLETTER = "email_newsletter"
    PRODUCT_DESCRIPTION = "product_description"
    LANDING_PAGE = "landing_page"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ContentRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    content_type: ContentType
    priority: Priority = Priority.MEDIUM
    target_audience: Optional[str] = None
    key_points: Optional[List[str]] = None
    tone: Optional[str] = None
    length: Optional[str] = None  # short, medium, long
    seo_keywords: Optional[List[str]] = None
    deadline: Optional[str] = None
    brand_voice: Optional[str] = None
    additional_context: Optional[str] = None


class ContentPlan(BaseModel):
    request_id: str
    title: str
    outline: List[str]
    target_keywords: List[str]
    word_count_target: int
    tone: str
    key_messages: List[str]
    research_notes: Optional[Dict[str, Any]] = None


class ContentDraft(BaseModel):
    request_id: str
    title: str
    content: str
    meta_description: Optional[str] = None
    tags: Optional[List[str]] = None
    word_count: int
    readability_score: Optional[float] = None


class QualityReport(BaseModel):
    request_id: str
    overall_score: float  # 0-100
    readability_score: float
    seo_score: float
    brand_voice_score: float
    issues: List[str]
    suggestions: List[str]
    approved: bool = False
