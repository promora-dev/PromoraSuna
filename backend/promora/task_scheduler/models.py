"""
Models for task scheduling in Promora.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from ..platform_publisher.models import PlatformType, PublishStatus


class TaskPriority(str, Enum):
    """Priority levels for scheduled tasks."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Status of a scheduled task."""
    
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Types of tasks that can be scheduled."""
    
    CONTENT_GENERATION = "content_generation"
    CONTENT_PUBLISHING = "content_publishing"
    ANALYTICS_COLLECTION = "analytics_collection"
    SYSTEM_MAINTENANCE = "system_maintenance"


class ScheduleType(str, Enum):
    """Types of scheduling for tasks."""
    
    IMMEDIATE = "immediate"
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class TaskSchedule(BaseModel):
    """Schedule configuration for a task."""
    
    schedule_type: ScheduleType
    scheduled_time: Optional[datetime] = None
    cron_expression: Optional[str] = None
    timezone: str = "UTC"
    
    class Config:
        arbitrary_types_allowed = True


class TaskDefinition(BaseModel):
    """Definition of a task to be scheduled."""
    
    task_id: str = Field(..., description="Unique identifier for the task")
    task_type: TaskType
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    schedule: TaskSchedule
    parameters: Dict[str, Any] = {}
    platforms: List[PlatformType] = []
    account_ids: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


class TaskExecution(BaseModel):
    """Execution record for a scheduled task."""
    
    execution_id: str = Field(..., description="Unique identifier for the execution")
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Dict[str, Any] = {}
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None
    platform_statuses: Dict[PlatformType, PublishStatus] = {}
    
    class Config:
        arbitrary_types_allowed = True


class TaskFilter(BaseModel):
    """Filter criteria for querying tasks."""
    
    task_ids: Optional[List[str]] = None
    task_types: Optional[List[TaskType]] = None
    statuses: Optional[List[TaskStatus]] = None
    priorities: Optional[List[TaskPriority]] = None
    platforms: Optional[List[PlatformType]] = None
    account_ids: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    scheduled_after: Optional[datetime] = None
    scheduled_before: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True
