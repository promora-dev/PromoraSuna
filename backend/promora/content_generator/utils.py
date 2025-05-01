"""
Utility functions for SEO content generation.
"""

import re
from typing import List, Dict, Any


def calculate_keyword_density(content: str, keywords: List[str]) -> Dict[str, float]:
    """Calculate keyword density in the content.
    
    Args:
        content: Content to analyze
        keywords: List of keywords to check
        
    Returns:
        Dictionary mapping keywords to their density percentage
    """
    clean_content = re.sub(r'<[^>]+>', '', content)
    
    total_words = len(clean_content.split())
    
    density = {}
    for keyword in keywords:
        count = len(re.findall(re.escape(keyword), clean_content, re.IGNORECASE))
        
        if total_words > 0:
            density[keyword] = (count / total_words) * 100
        else:
            density[keyword] = 0
    
    return density


def analyze_seo_factors(content: str, title: str, meta_description: str, keywords: List[str]) -> Dict[str, Any]:
    """Analyze SEO factors in the content.
    
    Args:
        content: Main content
        title: Content title
        meta_description: Meta description
        keywords: Target keywords
        
    Returns:
        Dictionary with SEO analysis results
    """
    clean_content = re.sub(r'<[^>]+>', '', content)
    
    word_count = len(clean_content.split())
    
    title_length = len(title)
    title_optimal = 50 <= title_length <= 60
    
    meta_length = len(meta_description)
    meta_optimal = 150 <= meta_length <= 160
    
    keywords_in_title = any(keyword.lower() in title.lower() for keyword in keywords)
    keywords_in_meta = any(keyword.lower() in meta_description.lower() for keyword in keywords)
    
    keyword_density = calculate_keyword_density(content, keywords)
    optimal_density = all(0.5 <= density <= 2.5 for density in keyword_density.values())
    
    has_h2 = bool(re.search(r'<h2[^>]*>.*?</h2>', content, re.IGNORECASE))
    has_h3 = bool(re.search(r'<h3[^>]*>.*?</h3>', content, re.IGNORECASE))
    
    return {
        "word_count": word_count,
        "title_length": title_length,
        "title_optimal": title_optimal,
        "meta_length": meta_length,
        "meta_optimal": meta_optimal,
        "keywords_in_title": keywords_in_title,
        "keywords_in_meta": keywords_in_meta,
        "keyword_density": keyword_density,
        "optimal_density": optimal_density,
        "has_h2": has_h2,
        "has_h3": has_h3
    }


def suggest_improvements(analysis: Dict[str, Any]) -> List[str]:
    """Suggest SEO improvements based on analysis.
    
    Args:
        analysis: SEO analysis results
        
    Returns:
        List of improvement suggestions
    """
    suggestions = []
    
    if analysis["word_count"] < 300:
        suggestions.append("增加内容长度，至少达到300字以上")
    
    if not analysis["title_optimal"]:
        if analysis["title_length"] < 50:
            suggestions.append("标题太短，建议增加到50-60个字符")
        elif analysis["title_length"] > 60:
            suggestions.append("标题太长，建议缩短到50-60个字符")
    
    if not analysis["meta_optimal"]:
        if analysis["meta_length"] < 150:
            suggestions.append("元描述太短，建议增加到150-160个字符")
        elif analysis["meta_length"] > 160:
            suggestions.append("元描述太长，建议缩短到150-160个字符")
    
    if not analysis["keywords_in_title"]:
        suggestions.append("在标题中添加主要关键词")
    
    if not analysis["keywords_in_meta"]:
        suggestions.append("在元描述中添加主要关键词")
    
    for keyword, density in analysis["keyword_density"].items():
        if density < 0.5:
            suggestions.append(f"关键词 '{keyword}' 密度太低，建议增加使用频率")
        elif density > 2.5:
            suggestions.append(f"关键词 '{keyword}' 密度太高，建议减少使用频率")
    
    if not analysis["has_h2"]:
        suggestions.append("添加H2标题以改善内容结构")
    
    if not analysis["has_h3"]:
        suggestions.append("添加H3子标题以改善内容层次")
    
    return suggestions
