"""
Analytics analyzer for Promora.

This module provides functionality for collecting and analyzing content performance data.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from utils.logger import logger
from ..platform_publisher.publisher import PlatformPublisher
from ..platform_publisher.models import PlatformType, PublishStatus
from .models import (
    MetricType,
    ContentPerformance,
    KeywordPerformance,
    AccountPerformance,
    AnalyticsReport,
    AnalyticsFilter
)


class AnalyticsAnalyzer:
    """Analyzer for collecting and analyzing content performance data."""
    
    def __init__(self, platform_publisher: PlatformPublisher):
        """Initialize the analytics analyzer.
        
        Args:
            platform_publisher: Platform publisher for accessing platform data
        """
        self.platform_publisher = platform_publisher
        self.content_performance: Dict[str, ContentPerformance] = {}
        self.keyword_performance: Dict[str, KeywordPerformance] = {}
        self.account_performance: Dict[str, AccountPerformance] = {}
    
    async def collect_content_performance(self, content_id: str) -> Optional[ContentPerformance]:
        """Collect performance data for a piece of content.
        
        Args:
            content_id: ID of the content to collect data for
            
        Returns:
            Performance data for the content, or None if not available
        """
        try:
            analytics = await self.platform_publisher.get_analytics(content_id)
            
            if not analytics:
                logger.warning(f"No analytics available for content {content_id}")
                return None
            
            result = self.platform_publisher.publish_results.get(content_id)
            
            if not result:
                logger.warning(f"No publish result found for content {content_id}")
                return None
            
            metrics = {}
            
            if "impressions" in analytics:
                metrics[MetricType.IMPRESSIONS] = analytics["impressions"]
            if "engagements" in analytics:
                metrics[MetricType.ENGAGEMENTS] = analytics["engagements"]
            if "likes" in analytics or "upvotes" in analytics or "claps" in analytics or "fans" in analytics:
                metrics[MetricType.LIKES] = analytics.get("likes", analytics.get("upvotes", analytics.get("claps", analytics.get("fans", 0))))
            if "comments" in analytics or "responses" in analytics:
                metrics[MetricType.COMMENTS] = analytics.get("comments", analytics.get("responses", 0))
            if "shares" in analytics or "retweets" in analytics:
                metrics[MetricType.SHARES] = analytics.get("shares", analytics.get("retweets", 0))
            if "clicks" in analytics:
                metrics[MetricType.CLICKS] = analytics["clicks"]
            if "views" in analytics or "reads" in analytics:
                metrics[MetricType.VIEWS] = analytics.get("views", analytics.get("reads", 0))
            
            performance = ContentPerformance(
                content_id=content_id,
                platform=result.platform,
                post_url=result.post_url or "",
                account_id=result.account_id,
                metrics=metrics,
                last_updated=datetime.now()
            )
            
            self.content_performance[content_id] = performance
            return performance
            
        except Exception as e:
            logger.error(f"Error collecting content performance for {content_id}: {e}")
            return None
    
    async def collect_keyword_performance(self, keyword: str) -> Optional[KeywordPerformance]:
        """Collect performance data for a keyword.
        
        Args:
            keyword: Keyword to collect data for
            
        Returns:
            Performance data for the keyword, or None if not available
        """
        try:
            
            existing_performance = self.keyword_performance.get(keyword)
            
            performance = KeywordPerformance(
                keyword=keyword,
                search_volume=1000,  # Placeholder
                difficulty=50,  # Placeholder
                current_rank=10,  # Placeholder
                previous_rank=existing_performance.current_rank if existing_performance else 15,  # Placeholder
                ranking_url="https://example.com/page",  # Placeholder
                last_updated=datetime.now()
            )
            
            self.keyword_performance[keyword] = performance
            return performance
            
        except Exception as e:
            logger.error(f"Error collecting keyword performance for {keyword}: {e}")
            return None
    
    async def collect_account_performance(self, account_id: str, platform: PlatformType) -> Optional[AccountPerformance]:
        """Collect performance data for a platform account.
        
        Args:
            account_id: ID of the account to collect data for
            platform: Platform the account is on
            
        Returns:
            Performance data for the account, or None if not available
        """
        try:
            
            if platform not in self.platform_publisher.platform_adapters:
                logger.warning(f"Platform {platform} not supported")
                return None
            
            if account_id not in self.platform_publisher.platform_adapters[platform]:
                logger.warning(f"Account {account_id} not found for platform {platform}")
                return None
            
            adapter = self.platform_publisher.platform_adapters[platform][account_id]
            
            performance = AccountPerformance(
                account_id=account_id,
                platform=platform,
                username=adapter.account.username,
                followers=1000,  # Placeholder
                total_posts=50,  # Placeholder
                total_engagements=5000,  # Placeholder
                engagement_rate=0.05,  # Placeholder
                last_updated=datetime.now()
            )
            
            self.account_performance[f"{platform}:{account_id}"] = performance
            return performance
            
        except Exception as e:
            logger.error(f"Error collecting account performance for {account_id} on {platform}: {e}")
            return None
    
    async def generate_report(
        self, 
        title: str, 
        description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        filter_criteria: Optional[AnalyticsFilter] = None
    ) -> AnalyticsReport:
        """Generate an analytics report.
        
        Args:
            title: Title for the report
            description: Description for the report
            start_date: Start date for the report period
            end_date: End date for the report period
            filter_criteria: Filter criteria to apply
            
        Returns:
            Generated analytics report
        """
        if not end_date:
            end_date = datetime.now()
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        content_performance = []
        for performance in self.content_performance.values():
            if performance.last_updated < start_date or performance.last_updated > end_date:
                continue
            
            if filter_criteria:
                if filter_criteria.content_ids and performance.content_id not in filter_criteria.content_ids:
                    continue
                
                if filter_criteria.platforms and performance.platform not in filter_criteria.platforms:
                    continue
                
                if filter_criteria.account_ids and performance.account_id not in filter_criteria.account_ids:
                    continue
            
            content_performance.append(performance)
        
        keyword_performance = []
        for performance in self.keyword_performance.values():
            if performance.last_updated < start_date or performance.last_updated > end_date:
                continue
            
            if filter_criteria and filter_criteria.keywords and performance.keyword not in filter_criteria.keywords:
                continue
            
            keyword_performance.append(performance)
        
        account_performance = []
        for performance in self.account_performance.values():
            if performance.last_updated < start_date or performance.last_updated > end_date:
                continue
            
            if filter_criteria:
                if filter_criteria.platforms and performance.platform not in filter_criteria.platforms:
                    continue
                
                if filter_criteria.account_ids and performance.account_id not in filter_criteria.account_ids:
                    continue
            
            account_performance.append(performance)
        
        summary_metrics = self._calculate_summary_metrics(
            content_performance, 
            keyword_performance, 
            account_performance
        )
        
        report = AnalyticsReport(
            report_id=str(uuid.uuid4()),
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            content_performance=content_performance,
            keyword_performance=keyword_performance,
            account_performance=account_performance,
            summary_metrics=summary_metrics,
            created_at=datetime.now()
        )
        
        return report
    
    def _calculate_summary_metrics(
        self,
        content_performance: List[ContentPerformance],
        keyword_performance: List[KeywordPerformance],
        account_performance: List[AccountPerformance]
    ) -> Dict[str, Any]:
        """Calculate summary metrics for a report.
        
        Args:
            content_performance: List of content performance records
            keyword_performance: List of keyword performance records
            account_performance: List of account performance records
            
        Returns:
            Dictionary of summary metrics
        """
        summary = {}
        
        total_impressions = sum(
            performance.metrics.get(MetricType.IMPRESSIONS, 0)
            for performance in content_performance
        )
        
        total_engagements = sum(
            performance.metrics.get(MetricType.ENGAGEMENTS, 0)
            for performance in content_performance
        )
        
        total_likes = sum(
            performance.metrics.get(MetricType.LIKES, 0)
            for performance in content_performance
        )
        
        total_comments = sum(
            performance.metrics.get(MetricType.COMMENTS, 0)
            for performance in content_performance
        )
        
        total_shares = sum(
            performance.metrics.get(MetricType.SHARES, 0)
            for performance in content_performance
        )
        
        total_clicks = sum(
            performance.metrics.get(MetricType.CLICKS, 0)
            for performance in content_performance
        )
        
        total_views = sum(
            performance.metrics.get(MetricType.VIEWS, 0)
            for performance in content_performance
        )
        
        engagement_rate = 0.0
        if total_impressions > 0:
            engagement_rate = total_engagements / total_impressions
        
        avg_keyword_rank = 0
        if keyword_performance:
            avg_keyword_rank = sum(
                performance.current_rank or 0
                for performance in keyword_performance
            ) / len(keyword_performance)
        
        total_followers = sum(
            performance.followers
            for performance in account_performance
        )
        
        summary["total_content"] = len(content_performance)
        summary["total_impressions"] = total_impressions
        summary["total_engagements"] = total_engagements
        summary["total_likes"] = total_likes
        summary["total_comments"] = total_comments
        summary["total_shares"] = total_shares
        summary["total_clicks"] = total_clicks
        summary["total_views"] = total_views
        summary["engagement_rate"] = engagement_rate
        summary["total_keywords"] = len(keyword_performance)
        summary["avg_keyword_rank"] = avg_keyword_rank
        summary["total_accounts"] = len(account_performance)
        summary["total_followers"] = total_followers
        
        platform_breakdown = {}
        for platform in PlatformType:
            platform_content = [p for p in content_performance if p.platform == platform]
            
            if platform_content:
                platform_impressions = sum(
                    p.metrics.get(MetricType.IMPRESSIONS, 0)
                    for p in platform_content
                )
                
                platform_engagements = sum(
                    p.metrics.get(MetricType.ENGAGEMENTS, 0)
                    for p in platform_content
                )
                
                platform_breakdown[platform.value] = {
                    "content_count": len(platform_content),
                    "impressions": platform_impressions,
                    "engagements": platform_engagements
                }
        
        summary["platform_breakdown"] = platform_breakdown
        
        return summary
    
    def get_content_performance(self, content_id: str) -> Optional[ContentPerformance]:
        """Get performance data for a piece of content.
        
        Args:
            content_id: ID of the content to get data for
            
        Returns:
            Performance data for the content, or None if not available
        """
        return self.content_performance.get(content_id)
    
    def get_keyword_performance(self, keyword: str) -> Optional[KeywordPerformance]:
        """Get performance data for a keyword.
        
        Args:
            keyword: Keyword to get data for
            
        Returns:
            Performance data for the keyword, or None if not available
        """
        return self.keyword_performance.get(keyword)
    
    def get_account_performance(self, account_id: str, platform: PlatformType) -> Optional[AccountPerformance]:
        """Get performance data for a platform account.
        
        Args:
            account_id: ID of the account to get data for
            platform: Platform the account is on
            
        Returns:
            Performance data for the account, or None if not available
        """
        return self.account_performance.get(f"{platform}:{account_id}")
    
    def get_all_content_performance(self, filter_criteria: Optional[AnalyticsFilter] = None) -> List[ContentPerformance]:
        """Get all content performance data matching the filter criteria.
        
        Args:
            filter_criteria: Filter criteria to apply
            
        Returns:
            List of matching content performance records
        """
        if not filter_criteria:
            return list(self.content_performance.values())
        
        filtered_performance = []
        
        for performance in self.content_performance.values():
            if filter_criteria.content_ids and performance.content_id not in filter_criteria.content_ids:
                continue
            
            if filter_criteria.platforms and performance.platform not in filter_criteria.platforms:
                continue
            
            if filter_criteria.account_ids and performance.account_id not in filter_criteria.account_ids:
                continue
            
            if filter_criteria.start_date and performance.last_updated < filter_criteria.start_date:
                continue
            
            if filter_criteria.end_date and performance.last_updated > filter_criteria.end_date:
                continue
            
            filtered_performance.append(performance)
        
        return filtered_performance
    
    def get_all_keyword_performance(self, filter_criteria: Optional[AnalyticsFilter] = None) -> List[KeywordPerformance]:
        """Get all keyword performance data matching the filter criteria.
        
        Args:
            filter_criteria: Filter criteria to apply
            
        Returns:
            List of matching keyword performance records
        """
        if not filter_criteria:
            return list(self.keyword_performance.values())
        
        filtered_performance = []
        
        for performance in self.keyword_performance.values():
            if filter_criteria.keywords and performance.keyword not in filter_criteria.keywords:
                continue
            
            if filter_criteria.start_date and performance.last_updated < filter_criteria.start_date:
                continue
            
            if filter_criteria.end_date and performance.last_updated > filter_criteria.end_date:
                continue
            
            filtered_performance.append(performance)
        
        return filtered_performance
    
    def get_all_account_performance(self, filter_criteria: Optional[AnalyticsFilter] = None) -> List[AccountPerformance]:
        """Get all account performance data matching the filter criteria.
        
        Args:
            filter_criteria: Filter criteria to apply
            
        Returns:
            List of matching account performance records
        """
        if not filter_criteria:
            return list(self.account_performance.values())
        
        filtered_performance = []
        
        for performance in self.account_performance.values():
            if filter_criteria.platforms and performance.platform not in filter_criteria.platforms:
                continue
            
            if filter_criteria.account_ids and performance.account_id not in filter_criteria.account_ids:
                continue
            
            if filter_criteria.start_date and performance.last_updated < filter_criteria.start_date:
                continue
            
            if filter_criteria.end_date and performance.last_updated > filter_criteria.end_date:
                continue
            
            filtered_performance.append(performance)
        
        return filtered_performance
