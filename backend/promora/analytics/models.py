"""
Models for analytics in Promora.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from ..platform_publisher.models import PlatformType


class MetricType(str, Enum):
    """Types of metrics that can be tracked."""
    
    IMPRESSIONS = "impressions"
    ENGAGEMENTS = "engagements"
    LIKES = "likes"
    COMMENTS = "comments"
    SHARES = "shares"
    CLICKS = "clicks"
    VIEWS = "views"
    FOLLOWERS = "followers"
    CONVERSIONS = "conversions"
    KEYWORD_RANK = "keyword_rank"


class ContentPerformance(BaseModel):
    """Performance metrics for a piece of content."""
    
    content_id: str = Field(..., description="ID of the content")
    platform: PlatformType
    post_url: str
    account_id: str
    metrics: Dict[MetricType, int] = {}
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True


class KeywordPerformance(BaseModel):
    """Performance metrics for a keyword."""
    
    keyword: str
    search_volume: Optional[int] = None
    difficulty: Optional[int] = None
    current_rank: Optional[int] = None
    previous_rank: Optional[int] = None
    ranking_url: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True


class AccountPerformance(BaseModel):
    """Performance metrics for a platform account."""
    
    account_id: str
    platform: PlatformType
    username: str
    followers: int = 0
    total_posts: int = 0
    total_engagements: int = 0
    engagement_rate: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True


class AnalyticsReport(BaseModel):
    """Comprehensive analytics report."""
    
    report_id: str = Field(..., description="Unique identifier for the report")
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    content_performance: List[ContentPerformance] = []
    keyword_performance: List[KeywordPerformance] = []
    account_performance: List[AccountPerformance] = []
    summary_metrics: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True


class AnalyticsFilter(BaseModel):
    """Filter criteria for querying analytics data."""
    
    content_ids: Optional[List[str]] = None
    platforms: Optional[List[PlatformType]] = None
    account_ids: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True
