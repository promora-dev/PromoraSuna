"""
Task scheduler for Promora.

This module provides functionality for scheduling and executing content publishing tasks.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import croniter
import pytz

from utils.logger import logger
from ..content_generator.seo_generator import SEOContentGenerator
from ..platform_publisher.publisher import PlatformPublisher
from ..platform_publisher.models import PublishRequest, PublishResult, PublishStatus, PlatformType
from .models import (
    TaskDefinition, 
    TaskExecution, 
    TaskStatus, 
    TaskType, 
    ScheduleType,
    TaskFilter,
    TaskSchedule
)


class TaskScheduler:
    """Scheduler for managing and executing tasks."""
    
    def __init__(
        self, 
        content_generator: SEOContentGenerator,
        platform_publisher: PlatformPublisher
    ):
        """Initialize the task scheduler.
        
        Args:
            content_generator: Content generator for generating content
            platform_publisher: Platform publisher for publishing content
        """
        self.content_generator = content_generator
        self.platform_publisher = platform_publisher
        self.tasks: Dict[str, TaskDefinition] = {}
        self.executions: Dict[str, TaskExecution] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.retry_delay = 300  # 5 minutes in seconds
        self.max_retries = 3
    
    async def schedule_task(self, task: TaskDefinition) -> TaskDefinition:
        """Schedule a task for execution.
        
        Args:
            task: Task definition to schedule
            
        Returns:
            The scheduled task definition
        """
        self.tasks[task.task_id] = task
        
        execution_id = str(uuid.uuid4())
        execution = TaskExecution(
            execution_id=execution_id,
            task_id=task.task_id,
            status=TaskStatus.SCHEDULED,
            max_retries=self.max_retries
        )
        self.executions[execution_id] = execution
        
        if task.schedule.schedule_type == ScheduleType.IMMEDIATE:
            asyncio.create_task(self._execute_task(execution_id))
        else:
            next_run_time = self._calculate_next_run_time(task.schedule)
            
            if next_run_time:
                now = datetime.now(pytz.timezone(task.schedule.timezone))
                delay = (next_run_time - now).total_seconds()
                
                if delay > 0:
                    self.running_tasks[execution_id] = asyncio.create_task(
                        self._schedule_delayed_execution(execution_id, delay)
                    )
                else:
                    asyncio.create_task(self._execute_task(execution_id))
        
        return task
    
    async def _schedule_delayed_execution(self, execution_id: str, delay: float) -> None:
        """Schedule a delayed execution of a task.
        
        Args:
            execution_id: ID of the execution to schedule
            delay: Delay in seconds before execution
        """
        await asyncio.sleep(delay)
        await self._execute_task(execution_id)
    
    async def _execute_task(self, execution_id: str) -> None:
        """Execute a scheduled task.
        
        Args:
            execution_id: ID of the execution to run
        """
        if execution_id not in self.executions:
            logger.error(f"Execution {execution_id} not found")
            return
        
        execution = self.executions[execution_id]
        task_id = execution.task_id
        
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            execution.status = TaskStatus.FAILED
            execution.error_message = f"Task {task_id} not found"
            self.executions[execution_id] = execution
            return
        
        task = self.tasks[task_id]
        
        execution.status = TaskStatus.RUNNING
        execution.started_at = datetime.now()
        self.executions[execution_id] = execution
        
        try:
            if task.task_type == TaskType.CONTENT_GENERATION:
                result = await self._execute_content_generation(task, execution)
            elif task.task_type == TaskType.CONTENT_PUBLISHING:
                result = await self._execute_content_publishing(task, execution)
            elif task.task_type == TaskType.ANALYTICS_COLLECTION:
                result = await self._execute_analytics_collection(task, execution)
            elif task.task_type == TaskType.SYSTEM_MAINTENANCE:
                result = await self._execute_system_maintenance(task, execution)
            else:
                raise ValueError(f"Unsupported task type: {task.task_type}")
            
            execution.status = TaskStatus.COMPLETED
            execution.completed_at = datetime.now()
            execution.result = result
            self.executions[execution_id] = execution
            
            if task.schedule.schedule_type not in [ScheduleType.IMMEDIATE, ScheduleType.ONCE]:
                self._schedule_next_execution(task)
                
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")
            
            execution.status = TaskStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            
            if execution.retry_count < execution.max_retries:
                execution.retry_count += 1
                execution.next_retry_at = datetime.now() + timedelta(seconds=self.retry_delay)
                execution.status = TaskStatus.RETRYING
                
                self.running_tasks[execution_id] = asyncio.create_task(
                    self._schedule_delayed_execution(execution_id, self.retry_delay)
                )
            
            self.executions[execution_id] = execution
    
    async def _execute_content_generation(
        self, 
        task: TaskDefinition, 
        execution: TaskExecution
    ) -> Dict[str, Any]:
        """Execute a content generation task.
        
        Args:
            task: Task definition
            execution: Task execution record
            
        Returns:
            Result of the content generation
        """
        logger.info(f"Executing content generation task: {task.title}")
        
        keyword = task.parameters.get("keyword", "")
        industry = task.parameters.get("industry", "")
        audience = task.parameters.get("audience", "")
        language = task.parameters.get("language", "en")
        
        content_result = await self.content_generator.generate_seo_content(
            keyword=keyword,
            industry=industry,
            audience=audience,
            language=language
        )
        
        summaries = {}
        for platform in task.platforms:
            summary = await self.content_generator.generate_platform_summary(
                content=content_result.content,
                platform=platform,
                language=language
            )
            summaries[platform] = summary
        
        return {
            "content": content_result.dict(),
            "summaries": {platform.value: summary.dict() for platform, summary in summaries.items()}
        }
    
    async def _execute_content_publishing(
        self, 
        task: TaskDefinition, 
        execution: TaskExecution
    ) -> Dict[str, Any]:
        """Execute a content publishing task.
        
        Args:
            task: Task definition
            execution: Task execution record
            
        Returns:
            Result of the content publishing
        """
        logger.info(f"Executing content publishing task: {task.title}")
        
        content_id = task.parameters.get("content_id", "")
        content = task.parameters.get("content", "")
        title = task.parameters.get("title", "")
        summaries = task.parameters.get("summaries", {})
        image_url = task.parameters.get("image_url", "")
        hashtags = task.parameters.get("hashtags", [])
        
        requests = []
        for platform in task.platforms:
            for account_id in task.account_ids:
                platform_content = summaries.get(platform.value, {}).get("content", content)
                
                request = PublishRequest(
                    platform=platform,
                    account_id=account_id,
                    content=platform_content,
                    title=title,
                    image_url=image_url,
                    hashtags=hashtags
                )
                requests.append(request)
        
        results = await self.platform_publisher.publish_to_multiple(requests)
        
        for result in results.values():
            execution.platform_statuses[result.platform] = result.status
        
        return {
            "publish_results": {result_id: result.dict() for result_id, result in results.items()}
        }
    
    async def _execute_analytics_collection(
        self, 
        task: TaskDefinition, 
        execution: TaskExecution
    ) -> Dict[str, Any]:
        """Execute an analytics collection task.
        
        Args:
            task: Task definition
            execution: Task execution record
            
        Returns:
            Result of the analytics collection
        """
        logger.info(f"Executing analytics collection task: {task.title}")
        
        post_ids = task.parameters.get("post_ids", [])
        
        analytics = {}
        for post_id in post_ids:
            post_analytics = await self.platform_publisher.get_analytics(post_id)
            if post_analytics:
                analytics[post_id] = post_analytics
        
        return {
            "analytics": analytics
        }
    
    async def _execute_system_maintenance(
        self, 
        task: TaskDefinition, 
        execution: TaskExecution
    ) -> Dict[str, Any]:
        """Execute a system maintenance task.
        
        Args:
            task: Task definition
            execution: Task execution record
            
        Returns:
            Result of the system maintenance
        """
        logger.info(f"Executing system maintenance task: {task.title}")
        
        await self.platform_publisher.process_retry_queue()
        
        
        return {
            "maintenance_completed": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_next_run_time(self, schedule: TaskSchedule) -> Optional[datetime]:
        """Calculate the next run time for a schedule.
        
        Args:
            schedule: Schedule configuration
            
        Returns:
            Next run time, or None if not applicable
        """
        now = datetime.now(pytz.timezone(schedule.timezone))
        
        if schedule.schedule_type == ScheduleType.IMMEDIATE:
            return now
        
        if schedule.schedule_type == ScheduleType.ONCE:
            return schedule.scheduled_time
        
        if schedule.schedule_type == ScheduleType.CUSTOM and schedule.cron_expression:
            cron = croniter.croniter(schedule.cron_expression, now)
            return cron.get_next(datetime)
        
        if schedule.schedule_type == ScheduleType.DAILY:
            if not schedule.scheduled_time:
                return now + timedelta(days=1)
            
            next_time = now.replace(
                hour=schedule.scheduled_time.hour,
                minute=schedule.scheduled_time.minute,
                second=schedule.scheduled_time.second
            )
            
            if next_time <= now:
                next_time += timedelta(days=1)
            
            return next_time
        
        if schedule.schedule_type == ScheduleType.WEEKLY:
            if not schedule.scheduled_time:
                return now + timedelta(weeks=1)
            
            days_ahead = schedule.scheduled_time.weekday() - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            next_time = now + timedelta(days=days_ahead)
            next_time = next_time.replace(
                hour=schedule.scheduled_time.hour,
                minute=schedule.scheduled_time.minute,
                second=schedule.scheduled_time.second
            )
            
            return next_time
        
        if schedule.schedule_type == ScheduleType.MONTHLY:
            if not schedule.scheduled_time:
                next_month = now.month + 1
                next_year = now.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                
                return now.replace(year=next_year, month=next_month)
            
            next_time = now.replace(
                day=min(schedule.scheduled_time.day, 28),  # Avoid month boundary issues
                hour=schedule.scheduled_time.hour,
                minute=schedule.scheduled_time.minute,
                second=schedule.scheduled_time.second
            )
            
            if next_time <= now:
                next_month = now.month + 1
                next_year = now.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                
                next_time = next_time.replace(year=next_year, month=next_month)
            
            return next_time
        
        return None
    
    def _schedule_next_execution(self, task: TaskDefinition) -> None:
        """Schedule the next execution of a recurring task.
        
        Args:
            task: Task definition to schedule
        """
        execution_id = str(uuid.uuid4())
        execution = TaskExecution(
            execution_id=execution_id,
            task_id=task.task_id,
            status=TaskStatus.SCHEDULED,
            max_retries=self.max_retries
        )
        self.executions[execution_id] = execution
        
        next_run_time = self._calculate_next_run_time(task.schedule)
        
        if next_run_time:
            now = datetime.now(pytz.timezone(task.schedule.timezone))
            delay = (next_run_time - now).total_seconds()
            
            if delay > 0:
                self.running_tasks[execution_id] = asyncio.create_task(
                    self._schedule_delayed_execution(execution_id, delay)
                )
            else:
                asyncio.create_task(self._execute_task(execution_id))
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if the task was cancelled, False otherwise
        """
        if task_id not in self.tasks:
            return False
        
        for execution_id, execution in self.executions.items():
            if execution.task_id == task_id and execution.status in [TaskStatus.SCHEDULED, TaskStatus.RETRYING]:
                if execution_id in self.running_tasks:
                    self.running_tasks[execution_id].cancel()
                    del self.running_tasks[execution_id]
                
                execution.status = TaskStatus.CANCELLED
                self.executions[execution_id] = execution
        
        return True
    
    def get_task(self, task_id: str) -> Optional[TaskDefinition]:
        """Get a task by ID.
        
        Args:
            task_id: ID of the task to get
            
        Returns:
            The task definition, or None if not found
        """
        return self.tasks.get(task_id)
    
    def get_execution(self, execution_id: str) -> Optional[TaskExecution]:
        """Get an execution by ID.
        
        Args:
            execution_id: ID of the execution to get
            
        Returns:
            The execution record, or None if not found
        """
        return self.executions.get(execution_id)
    
    def get_executions_for_task(self, task_id: str) -> List[TaskExecution]:
        """Get all executions for a task.
        
        Args:
            task_id: ID of the task to get executions for
            
        Returns:
            List of execution records for the task
        """
        return [
            execution for execution in self.executions.values()
            if execution.task_id == task_id
        ]
    
    def get_tasks(self, filter_criteria: Optional[TaskFilter] = None) -> List[TaskDefinition]:
        """Get tasks matching the filter criteria.
        
        Args:
            filter_criteria: Filter criteria to apply
            
        Returns:
            List of matching task definitions
        """
        if not filter_criteria:
            return list(self.tasks.values())
        
        filtered_tasks = []
        
        for task in self.tasks.values():
            if filter_criteria.task_ids and task.task_id not in filter_criteria.task_ids:
                continue
            
            if filter_criteria.task_types and task.task_type not in filter_criteria.task_types:
                continue
            
            if filter_criteria.priorities and task.priority not in filter_criteria.priorities:
                continue
            
            if filter_criteria.platforms and not any(platform in filter_criteria.platforms for platform in task.platforms):
                continue
            
            if filter_criteria.account_ids and not any(account_id in filter_criteria.account_ids for account_id in task.account_ids):
                continue
            
            if filter_criteria.created_after and task.created_at < filter_criteria.created_after:
                continue
            
            if filter_criteria.created_before and task.created_at > filter_criteria.created_before:
                continue
            
            if filter_criteria.scheduled_after and task.schedule.scheduled_time and task.schedule.scheduled_time < filter_criteria.scheduled_after:
                continue
            
            if filter_criteria.scheduled_before and task.schedule.scheduled_time and task.schedule.scheduled_time > filter_criteria.scheduled_before:
                continue
            
            filtered_tasks.append(task)
        
        return filtered_tasks
    
    def get_executions(self, filter_criteria: Optional[TaskFilter] = None) -> List[TaskExecution]:
        """Get executions matching the filter criteria.
        
        Args:
            filter_criteria: Filter criteria to apply
            
        Returns:
            List of matching execution records
        """
        if not filter_criteria:
            return list(self.executions.values())
        
        filtered_executions = []
        
        for execution in self.executions.values():
            if execution.task_id not in self.tasks:
                continue
            
            task = self.tasks[execution.task_id]
            
            if filter_criteria.task_ids and execution.task_id not in filter_criteria.task_ids:
                continue
            
            if filter_criteria.task_types and task.task_type not in filter_criteria.task_types:
                continue
            
            if filter_criteria.statuses and execution.status not in filter_criteria.statuses:
                continue
            
            if filter_criteria.priorities and task.priority not in filter_criteria.priorities:
                continue
            
            if filter_criteria.platforms and not any(platform in filter_criteria.platforms for platform in task.platforms):
                continue
            
            if filter_criteria.account_ids and not any(account_id in filter_criteria.account_ids for account_id in task.account_ids):
                continue
            
            filtered_executions.append(execution)
        
        return filtered_executions
