"""
API router for Promora.

This module provides FastAPI routers for the Promora API.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime

from utils.logger import logger

from ..content_generator.seo_generator import SEOContentGenerator
from ..content_generator.models import ContentGenerationRequest, ContentGenerationResult, PlatformSummaryRequest
from ..platform_publisher.publisher import PlatformPublisher
from ..platform_publisher.human_registration import HumanRegistration
from ..platform_publisher.models import (
    PublishRequest, 
    PublishResult, 
    PlatformAccount, 
    PlatformType,
    PublishStatus,
    SocialActionRequest,
    SocialActionResult,
    SocialActionType,
    SocialActionStatus
)
from ..task_scheduler.scheduler import TaskScheduler
from ..task_scheduler.models import (
    TaskDefinition,
    TaskExecution,
    TaskStatus,
    TaskType,
    ScheduleType,
    TaskSchedule,
    TaskFilter
)
from ..analytics.analyzer import AnalyticsAnalyzer
from ..analytics.models import (
    ContentPerformance,
    KeywordPerformance,
    AccountPerformance,
    AnalyticsReport,
    AnalyticsFilter
)


content_router = APIRouter(prefix="/content", tags=["content"])
platform_router = APIRouter(prefix="/platform", tags=["platform"])
task_router = APIRouter(prefix="/task", tags=["task"])
analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_content_generator():
    return SEOContentGenerator()


def get_platform_publisher():
    return PlatformPublisher()


def get_human_registration():
    try:
        from agent.tools.sb_browser_tool import SandboxBrowserTool
        browser_tool = SandboxBrowserTool()
        
        from ..platform_publisher.email_client import EmailClientFactory
        import os
        
        email_address = os.getenv("EMAIL_ADDRESS")
        email_password = os.getenv("EMAIL_PASSWORD")
        email_provider = os.getenv("EMAIL_PROVIDER", "gmail")
        
        email_client = None
        if email_address and email_password:
            email_client = EmailClientFactory.create_client(
                email_address=email_address,
                password=email_password,
                provider=email_provider
            )
            if not email_client.connect():
                logger.warning("Failed to connect to email server")
                email_client = None
        
        return HumanRegistration(browser_tool, email_client=email_client)
    except Exception as e:
        logger.warning(f"Could not initialize SandboxBrowserTool: {e}")
        return HumanRegistration()


def get_task_scheduler():
    content_generator = get_content_generator()
    platform_publisher = get_platform_publisher()
    return TaskScheduler(content_generator, platform_publisher)


def get_analytics_analyzer():
    platform_publisher = get_platform_publisher()
    return AnalyticsAnalyzer(platform_publisher)


@content_router.post("/generate", response_model=ContentGenerationResult)
async def generate_content(
    request: ContentGenerationRequest,
    content_generator: SEOContentGenerator = Depends(get_content_generator)
):
    """Generate SEO-optimized content."""
    try:
        result = await content_generator.generate_seo_content(
            keyword=request.keyword,
            industry=request.industry,
            audience=request.audience,
            language=request.language
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@content_router.post("/generate-summary", response_model=Dict[str, Any])
async def generate_platform_summary(
    request: PlatformSummaryRequest,
    content_generator: SEOContentGenerator = Depends(get_content_generator)
):
    """Generate platform-specific summary."""
    try:
        summary = await content_generator.generate_platform_summary(
            content=request.content,
            platform=request.platform,
            language=request.language
        )
        return summary.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@platform_router.post("/accounts", response_model=Dict[str, Any])
async def register_account(
    account: PlatformAccount,
    platform_publisher: PlatformPublisher = Depends(get_platform_publisher)
):
    """Register a platform account."""
    try:
        platform_publisher.register_account(account)
        return {"success": True, "message": f"Account registered: {account.username}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@platform_router.post("/human-register/x", response_model=Dict[str, Any])
async def human_register_x_account(
    username: str,
    email: str,
    password: str,
    display_name: Optional[str] = None,
    verification_email: Optional[str] = None,
    verification_email_password: Optional[str] = None,
    verification_email_provider: Optional[str] = "gmail",
    human_registration: HumanRegistration = Depends(get_human_registration)
):
    """Register an X account with human-like behavior."""
    try:
        email_client = None
        if verification_email and verification_email_password:
            from ..platform_publisher.email_client import EmailClientFactory
            email_client = EmailClientFactory.create_client(
                email_address=verification_email,
                password=verification_email_password,
                provider=verification_email_provider
            )
            if not email_client.connect():
                logger.warning("Failed to connect to email server with provided credentials")
                email_client = None
        
        # Use the provided email client or the default one from HumanRegistration
        if email_client:
            human_registration.email_client = email_client
        
        account = await human_registration.register_x_account(
            username=username,
            email=email,
            password=password,
            display_name=display_name
        )
        
        if account:
            platform_publisher = get_platform_publisher()
            platform_publisher.register_account(account)
            
            return {
                "success": True, 
                "message": f"X account registered with human-like behavior: {username}",
                "account": account.dict()
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail="Failed to register X account. Check logs for details."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@platform_router.post("/human-register/zhihu", response_model=Dict[str, Any])
async def human_register_zhihu_account(
    username: str,
    email: str,
    password: str,
    display_name: Optional[str] = None,
    verification_email: Optional[str] = None,
    verification_email_password: Optional[str] = None,
    verification_email_provider: Optional[str] = "gmail",
    human_registration: HumanRegistration = Depends(get_human_registration)
):
    """Register a Zhihu account with human-like behavior."""
    try:
        email_client = None
        if verification_email and verification_email_password:
            from ..platform_publisher.email_client import EmailClientFactory
            email_client = EmailClientFactory.create_client(
                email_address=verification_email,
                password=verification_email_password,
                provider=verification_email_provider
            )
            if not email_client.connect():
                logger.warning("Failed to connect to email server with provided credentials")
                email_client = None
        
        # Use the provided email client or the default one from HumanRegistration
        if email_client:
            human_registration.email_client = email_client
        
        account = await human_registration.register_zhihu_account(
            username=username,
            email=email,
            password=password,
            display_name=display_name
        )
        
        if account:
            platform_publisher = get_platform_publisher()
            platform_publisher.register_account(account)
            
            return {
                "success": True, 
                "message": f"Zhihu account registered with human-like behavior: {username}",
                "account": account.dict()
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail="Failed to register Zhihu account. Check logs for details."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@platform_router.post("/human-register/medium", response_model=Dict[str, Any])
async def human_register_medium_account(
    username: str,
    email: str,
    password: str,
    display_name: Optional[str] = None,
    verification_email: Optional[str] = None,
    verification_email_password: Optional[str] = None,
    verification_email_provider: Optional[str] = "gmail",
    human_registration: HumanRegistration = Depends(get_human_registration)
):
    """Register a Medium account with human-like behavior."""
    try:
        email_client = None
        if verification_email and verification_email_password:
            from ..platform_publisher.email_client import EmailClientFactory
            email_client = EmailClientFactory.create_client(
                email_address=verification_email,
                password=verification_email_password,
                provider=verification_email_provider
            )
            if not email_client.connect():
                logger.warning("Failed to connect to email server with provided credentials")
                email_client = None
        
        # Use the provided email client or the default one from HumanRegistration
        if email_client:
            human_registration.email_client = email_client
        
        account = await human_registration.register_medium_account(
            username=username,
            email=email,
            password=password,
            display_name=display_name
        )
        
        if account:
            platform_publisher = get_platform_publisher()
            platform_publisher.register_account(account)
            
            return {
                "success": True, 
                "message": f"Medium account registered with human-like behavior: {username}",
                "account": account.dict()
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail="Failed to register Medium account. Check logs for details."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@platform_router.post("/human-register/linkedin", response_model=Dict[str, Any])
async def human_register_linkedin_account(
    username: str,
    email: str,
    password: str,
    display_name: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    verification_email: Optional[str] = None,
    verification_email_password: Optional[str] = None,
    verification_email_provider: Optional[str] = "gmail",
    human_registration: HumanRegistration = Depends(get_human_registration)
):
    """Register a LinkedIn account with human-like behavior."""
    try:
        email_client = None
        if verification_email and verification_email_password:
            from ..platform_publisher.email_client import EmailClientFactory
            email_client = EmailClientFactory.create_client(
                email_address=verification_email,
                password=verification_email_password,
                provider=verification_email_provider
            )
            if not email_client.connect():
                logger.warning("Failed to connect to email server with provided credentials")
                email_client = None
        
        # Use the provided email client or the default one from HumanRegistration
        if email_client:
            human_registration.email_client = email_client
        
        account = await human_registration.register_linkedin_account(
            username=username,
            email=email,
            password=password,
            display_name=display_name,
            first_name=first_name,
            last_name=last_name
        )
        
        if account:
            platform_publisher = get_platform_publisher()
            platform_publisher.register_account(account)
            
            return {
                "success": True, 
                "message": f"LinkedIn account registered with human-like behavior: {username}",
                "account": account.dict()
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail="Failed to register LinkedIn account. Check logs for details."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@platform_router.post("/publish", response_model=PublishResult)
async def publish_content(
    request: PublishRequest,
    platform_publisher: PlatformPublisher = Depends(get_platform_publisher)
):
    """Publish content to a platform."""
    try:
        result = await platform_publisher.publish(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@platform_router.post("/publish-multiple", response_model=Dict[str, PublishResult])
async def publish_to_multiple(
    requests: List[PublishRequest],
    platform_publisher: PlatformPublisher = Depends(get_platform_publisher)
):
    """Publish content to multiple platforms."""
    try:
        results = await platform_publisher.publish_to_multiple(requests)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@platform_router.get("/status/{request_id}", response_model=Dict[str, Any])
async def check_publish_status(
    request_id: str,
    platform_publisher: PlatformPublisher = Depends(get_platform_publisher)
):
    """Check the status of a publishing operation."""
    try:
        status = await platform_publisher.check_status(request_id)
        return {"request_id": request_id, "status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@platform_router.get("/requirements", response_model=Dict[PlatformType, Dict[str, Any]])
async def get_platform_requirements(
    platform_publisher: PlatformPublisher = Depends(get_platform_publisher)
):
    """Get content requirements for all supported platforms."""
    try:
        requirements = platform_publisher.get_all_platform_requirements()
        return requirements
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@platform_router.post("/social-action", response_model=SocialActionResult)
async def social_action(
    request: SocialActionRequest,
    platform_publisher: PlatformPublisher = Depends(get_platform_publisher)
):
    """Perform a social interaction on a platform (like, reply, retweet, quote)."""
    try:
        result = await platform_publisher.social_action(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@platform_router.post("/social-action-multiple", response_model=Dict[str, SocialActionResult])
async def social_action_multiple(
    requests: List[SocialActionRequest],
    platform_publisher: PlatformPublisher = Depends(get_platform_publisher)
):
    """Perform multiple social interactions on platforms."""
    try:
        results = await platform_publisher.social_action_to_multiple(requests)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@task_router.post("/schedule", response_model=TaskDefinition)
async def schedule_task(
    task: TaskDefinition,
    task_scheduler: TaskScheduler = Depends(get_task_scheduler)
):
    """Schedule a task for execution."""
    try:
        result = await task_scheduler.schedule_task(task)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@task_router.post("/cancel/{task_id}", response_model=Dict[str, Any])
async def cancel_task(
    task_id: str,
    task_scheduler: TaskScheduler = Depends(get_task_scheduler)
):
    """Cancel a scheduled task."""
    try:
        success = task_scheduler.cancel_task(task_id)
        if success:
            return {"success": True, "message": f"Task {task_id} cancelled"}
        else:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@task_router.get("/task/{task_id}", response_model=TaskDefinition)
async def get_task(
    task_id: str,
    task_scheduler: TaskScheduler = Depends(get_task_scheduler)
):
    """Get a task by ID."""
    try:
        task = task_scheduler.get_task(task_id)
        if task:
            return task
        else:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@task_router.get("/execution/{execution_id}", response_model=TaskExecution)
async def get_execution(
    execution_id: str,
    task_scheduler: TaskScheduler = Depends(get_task_scheduler)
):
    """Get an execution by ID."""
    try:
        execution = task_scheduler.get_execution(execution_id)
        if execution:
            return execution
        else:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@task_router.get("/executions/{task_id}", response_model=List[TaskExecution])
async def get_executions_for_task(
    task_id: str,
    task_scheduler: TaskScheduler = Depends(get_task_scheduler)
):
    """Get all executions for a task."""
    try:
        executions = task_scheduler.get_executions_for_task(task_id)
        return executions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@task_router.post("/tasks", response_model=List[TaskDefinition])
async def get_tasks(
    filter_criteria: Optional[TaskFilter] = None,
    task_scheduler: TaskScheduler = Depends(get_task_scheduler)
):
    """Get tasks matching the filter criteria."""
    try:
        tasks = task_scheduler.get_tasks(filter_criteria)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@task_router.post("/executions", response_model=List[TaskExecution])
async def get_executions(
    filter_criteria: Optional[TaskFilter] = None,
    task_scheduler: TaskScheduler = Depends(get_task_scheduler)
):
    """Get executions matching the filter criteria."""
    try:
        executions = task_scheduler.get_executions(filter_criteria)
        return executions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post("/collect-content/{content_id}", response_model=ContentPerformance)
async def collect_content_performance(
    content_id: str,
    background_tasks: BackgroundTasks,
    analytics_analyzer: AnalyticsAnalyzer = Depends(get_analytics_analyzer)
):
    """Collect performance data for a piece of content."""
    try:
        background_tasks.add_task(analytics_analyzer.collect_content_performance, content_id)
        return {"message": f"Content performance collection started for {content_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post("/collect-keyword/{keyword}", response_model=KeywordPerformance)
async def collect_keyword_performance(
    keyword: str,
    background_tasks: BackgroundTasks,
    analytics_analyzer: AnalyticsAnalyzer = Depends(get_analytics_analyzer)
):
    """Collect performance data for a keyword."""
    try:
        background_tasks.add_task(analytics_analyzer.collect_keyword_performance, keyword)
        return {"message": f"Keyword performance collection started for {keyword}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post("/collect-account", response_model=AccountPerformance)
async def collect_account_performance(
    account_id: str,
    platform: PlatformType,
    background_tasks: BackgroundTasks,
    analytics_analyzer: AnalyticsAnalyzer = Depends(get_analytics_analyzer)
):
    """Collect performance data for a platform account."""
    try:
        background_tasks.add_task(
            analytics_analyzer.collect_account_performance, 
            account_id, 
            platform
        )
        return {"message": f"Account performance collection started for {account_id} on {platform}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post("/report", response_model=AnalyticsReport)
async def generate_report(
    title: str,
    description: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    filter_criteria: Optional[AnalyticsFilter] = None,
    analytics_analyzer: AnalyticsAnalyzer = Depends(get_analytics_analyzer)
):
    """Generate an analytics report."""
    try:
        report = await analytics_analyzer.generate_report(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            filter_criteria=filter_criteria
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get("/content/{content_id}", response_model=ContentPerformance)
async def get_content_performance(
    content_id: str,
    analytics_analyzer: AnalyticsAnalyzer = Depends(get_analytics_analyzer)
):
    """Get performance data for a piece of content."""
    try:
        performance = analytics_analyzer.get_content_performance(content_id)
        if performance:
            return performance
        else:
            raise HTTPException(status_code=404, detail=f"Content performance for {content_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get("/keyword/{keyword}", response_model=KeywordPerformance)
async def get_keyword_performance(
    keyword: str,
    analytics_analyzer: AnalyticsAnalyzer = Depends(get_analytics_analyzer)
):
    """Get performance data for a keyword."""
    try:
        performance = analytics_analyzer.get_keyword_performance(keyword)
        if performance:
            return performance
        else:
            raise HTTPException(status_code=404, detail=f"Keyword performance for {keyword} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get("/account/{platform}/{account_id}", response_model=AccountPerformance)
async def get_account_performance(
    platform: PlatformType,
    account_id: str,
    analytics_analyzer: AnalyticsAnalyzer = Depends(get_analytics_analyzer)
):
    """Get performance data for a platform account."""
    try:
        performance = analytics_analyzer.get_account_performance(account_id, platform)
        if performance:
            return performance
        else:
            raise HTTPException(status_code=404, detail=f"Account performance for {account_id} on {platform} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post("/content", response_model=List[ContentPerformance])
async def get_all_content_performance(
    filter_criteria: Optional[AnalyticsFilter] = None,
    analytics_analyzer: AnalyticsAnalyzer = Depends(get_analytics_analyzer)
):
    """Get all content performance data matching the filter criteria."""
    try:
        performance = analytics_analyzer.get_all_content_performance(filter_criteria)
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post("/keywords", response_model=List[KeywordPerformance])
async def get_all_keyword_performance(
    filter_criteria: Optional[AnalyticsFilter] = None,
    analytics_analyzer: AnalyticsAnalyzer = Depends(get_analytics_analyzer)
):
    """Get all keyword performance data matching the filter criteria."""
    try:
        performance = analytics_analyzer.get_all_keyword_performance(filter_criteria)
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post("/accounts", response_model=List[AccountPerformance])
async def get_all_account_performance(
    filter_criteria: Optional[AnalyticsFilter] = None,
    analytics_analyzer: AnalyticsAnalyzer = Depends(get_analytics_analyzer)
):
    """Get all account performance data matching the filter criteria."""
    try:
        performance = analytics_analyzer.get_all_account_performance(filter_criteria)
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
