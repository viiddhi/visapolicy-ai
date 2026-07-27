from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class RuleChangeResponse(BaseModel):
    id: str
    document_id: str
    document_title: Optional[str] = None
    document_source_url: Optional[str] = None
    section: Optional[str]
    topic: str
    old_rule: str
    new_rule: str
    plain_english_summary: str
    impact_level: str
    action_required: bool
    action_description: Optional[str]
    visa_categories_affected: Optional[list[str]]
    who_is_affected: Optional[list[str]]
    tags: Optional[list[str]]
    published_at: Optional[date] = None
    effective_at: Optional[date] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedItem(BaseModel):
    relevance_score: float
    relevance_reasons: list[str]
    change: RuleChangeResponse


class DashboardStats(BaseModel):
    total_relevant: int
    high_impact: int
    action_required: int


class DashboardResponse(BaseModel):
    feed: list[FeedItem]
    stats: DashboardStats
