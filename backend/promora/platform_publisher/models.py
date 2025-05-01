"""
Data models for platform publishing in Promora.
"""

from typing import List, Dict, Optional, Any, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class PublishStatus(str, Enum):
    """Status of a publishing task."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class PlatformType(str, Enum):
    """Supported platform types."""
    
    X = "x"
    LINKEDIN = "linkedin"
    MEDIUM = "medium"
    ZHIHU = "zhihu"


class PublishRequest(BaseModel):
    """Request model for content publishing."""
    
    content_id: str = Field(
        ..., 
        description="ID of the content to publish"
    )
    platform: PlatformType = Field(
        ..., 
        description="Platform to publish to"
    )
    account_id: str = Field(
        ..., 
        description="ID of the account to use for publishing"
    )
    content: str = Field(
        ..., 
        description="Content to publish"
    )
    title: Optional[str] = Field(
        default=None, 
        description="Title for the content (required for some platforms)"
    )
    hashtags: Optional[List[str]] = Field(
        default=None, 
        description="Hashtags to include in the post"
    )
    image_url: Optional[str] = Field(
        default=None, 
        description="URL of an image to include with the post"
    )
    scheduled_time: Optional[datetime] = Field(
        default=None, 
        description="Time to publish the content (if scheduled)"
    )


class PublishResult(BaseModel):
    """Result model for content publishing."""
    
    request_id: str = Field(
        ..., 
        description="ID of the publish request"
    )
    platform: PlatformType = Field(
        ..., 
        description="Platform published to"
    )
    account_id: str = Field(
        ..., 
        description="ID of the account used for publishing"
    )
    status: PublishStatus = Field(
        ..., 
        description="Status of the publishing task"
    )
    post_url: Optional[str] = Field(
        default=None, 
        description="URL of the published post (if successful)"
    )
    error_message: Optional[str] = Field(
        default=None, 
        description="Error message (if failed)"
    )
    published_at: Optional[datetime] = Field(
        default=None, 
        description="Time the content was published"
    )
    screenshots: Optional[List[str]] = Field(
        default=None, 
        description="Screenshots of the publishing process"
    )


class PlatformAccount(BaseModel):
    """Model for platform account information."""
    
    account_id: str = Field(
        ..., 
        description="Unique identifier for the account"
    )
    platform: PlatformType = Field(
        ..., 
        description="Platform this account is for"
    )
    username: str = Field(
        ..., 
        description="Username for the account"
    )
    display_name: Optional[str] = Field(
        default=None, 
        description="Display name for the account"
    )
    auth_type: str = Field(
        ..., 
        description="Type of authentication (api_key, oauth, credentials)"
    )
    auth_data: Dict[str, Any] = Field(
        ..., 
        description="Authentication data for the account"
    )
    last_used: Optional[datetime] = Field(
        default=None, 
        description="Last time this account was used"
    )
    usage_count: int = Field(
        default=0, 
        description="Number of times this account has been used"
    )
    status: str = Field(
        default="active", 
        description="Status of the account (active, rate_limited, disabled)"
    )
