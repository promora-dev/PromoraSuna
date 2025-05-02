"""
Main application for Promora.

This module provides the main FastAPI application for the Promora system.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Dict, Any, Optional

try:
    from agent.tools.sb_browser_tool import SandboxBrowserTool
    has_browser_tool = True
except ImportError:
    has_browser_tool = False
    
from ..content_generator.seo_generator import SEOContentGenerator
from ..platform_publisher.publisher import PlatformPublisher
from ..task_scheduler.scheduler import TaskScheduler
from ..analytics.analyzer import AnalyticsAnalyzer
from .router import content_router, platform_router, task_router, analytics_router, verification_router
from .router import get_content_generator, get_platform_publisher, get_task_scheduler, get_analytics_analyzer


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Promora API",
        description="API for Promora - AI-driven virtual CMO for automated content marketing and SEO growth",
        version="1.0.0"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, this should be restricted
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    content_generator = SEOContentGenerator()
    
    browser_tool = None
    if has_browser_tool:
        try:
            browser_tool = SandboxBrowserTool()
        except Exception as e:
            print(f"Warning: Could not initialize SandboxBrowserTool: {e}")
    
    platform_publisher = PlatformPublisher(browser_tool=browser_tool)
    task_scheduler = TaskScheduler(content_generator, platform_publisher)
    analytics_analyzer = AnalyticsAnalyzer(platform_publisher)
    
    app.dependency_overrides[get_content_generator] = lambda: content_generator
    app.dependency_overrides[get_platform_publisher] = lambda: platform_publisher
    app.dependency_overrides[get_task_scheduler] = lambda: task_scheduler
    app.dependency_overrides[get_analytics_analyzer] = lambda: analytics_analyzer
    
    app.include_router(content_router)
    app.include_router(platform_router)
    app.include_router(task_router)
    app.include_router(analytics_router)
    app.include_router(verification_router)
    
    @app.get("/", response_model=Dict[str, Any])
    async def root():
        """Root endpoint for the API."""
        return {
            "name": "Promora API",
            "version": "1.0.0",
            "description": "AI-driven virtual CMO for automated content marketing and SEO growth"
        }
    
    @app.get("/health", response_model=Dict[str, Any])
    async def health():
        """Health check endpoint."""
        return {"status": "healthy"}
    
    return app


app = create_app()
