"""
Data models for content generation in Promora.
"""

from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field

from ..platform_publisher.models import PlatformType


class ContentRequest(BaseModel):
    """Request model for content generation."""
    
    keywords: List[str] = Field(
        ..., 
        description="Primary keywords to target in the content"
    )
    industry: str = Field(
        ..., 
        description="Industry or niche for the content"
    )
    audience: str = Field(
        ..., 
        description="Target audience for the content"
    )
    content_type: str = Field(
        ..., 
        description="Type of content to generate (article, blog post, social media)"
    )
    language: str = Field(
        default="en", 
        description="Language for the content (en, zh, ko, ja)"
    )
    brand_materials: Optional[List[str]] = Field(
        default=None, 
        description="Optional brand materials or existing content fragments"
    )
    tone: str = Field(
        default="professional", 
        description="Tone of the content (professional, casual, technical)"
    )
    length: str = Field(
        default="medium", 
        description="Length of the content (short, medium, long)"
    )


class PlatformSummary(BaseModel):
    """Model for platform-specific content summary."""
    
    platform: str = Field(
        ..., 
        description="Platform name (X, LinkedIn, Medium, Zhihu, etc.)"
    )
    content: str = Field(
        ..., 
        description="Platform-specific content summary"
    )
    hashtags: Optional[List[str]] = Field(
        default=None, 
        description="Relevant hashtags for the platform"
    )
    image_prompt: Optional[str] = Field(
        default=None, 
        description="Prompt for generating an image for this content"
    )


class GeneratedContent(BaseModel):
    """Model for generated content."""
    
    title: str = Field(
        ..., 
        description="Title of the content"
    )
    main_content: str = Field(
        ..., 
        description="Main content body"
    )
    meta_description: str = Field(
        ..., 
        description="SEO meta description"
    )
    keywords: List[str] = Field(
        ..., 
        description="Keywords used in the content"
    )
    summaries: List[PlatformSummary] = Field(
        ..., 
        description="Platform-specific summaries"
    )
    language: str = Field(
        ..., 
        description="Language of the content"
    )


class ContentGenerationRequest(BaseModel):
    """Request model for SEO content generation."""
    
    keyword: str = Field(
        ..., 
        description="Primary keyword to target in the content"
    )
    industry: str = Field(
        ..., 
        description="Industry or niche for the content"
    )
    audience: str = Field(
        ..., 
        description="Target audience for the content"
    )
    language: str = Field(
        default="en", 
        description="Language for the content (en, zh, ko, ja)"
    )
    brand_materials: Optional[List[str]] = Field(
        default=None, 
        description="Optional brand materials or existing content fragments"
    )
    tone: str = Field(
        default="professional", 
        description="Tone of the content (professional, casual, technical)"
    )
    length: str = Field(
        default="medium", 
        description="Length of the content (short, medium, long)"
    )


class ContentGenerationResult(BaseModel):
    """Result model for SEO content generation."""
    
    content_id: str = Field(
        ..., 
        description="Unique identifier for the generated content"
    )
    content: GeneratedContent = Field(
        ..., 
        description="Generated content"
    )
    generated_at: str = Field(
        ..., 
        description="Timestamp when the content was generated"
    )


class PlatformSummaryRequest(BaseModel):
    """Request model for platform-specific summary generation."""
    
    content: str = Field(
        ..., 
        description="Original content to summarize"
    )
    platform: PlatformType = Field(
        ..., 
        description="Platform to generate summary for"
    )
    language: str = Field(
        default="en", 
        description="Language for the summary (en, zh, ko, ja)"
    )
    max_length: Optional[int] = Field(
        default=None, 
        description="Maximum length of the summary in characters"
    )
