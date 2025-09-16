import re
from typing import List, Dict
import yake
from urllib.parse import quote_plus
import requests
from config.logging_config import get_logger


class SEOAnalyzer:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.keyword_extractor = yake.KeywordExtractor(
            lan="en", n=3, dedupLim=0.7, top=10
        )
        self.logger.info("SEO Analyzer initialized")

    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text using YAKE"""
        self.logger.debug(f"Extracting keywords from {len(text)} characters")

        try:
            keywords = self.keyword_extractor.extract_keywords(text)
            # YAKE returns (keyword, score) tuples, we want the keyword (index 0)
            result = [str(kw[0]) for kw in keywords]
            self.logger.debug(
                f"Extracted {len(result)} keywords: {result[:5]}"
            )  # Log first 5
            return result
        except Exception as e:
            self.logger.error(f"Keyword extraction failed: {e}", exc_info=True)
            return []

    def analyze_content(self, content: str, title: str, keywords: List[str]) -> float:
        """Analyze content for SEO score (0-100)"""
        self.logger.debug(
            f"Analyzing SEO for content: {len(content)} chars, title: {title}, keywords: {len(keywords)}"
        )

        score = 0
        max_score = 100

        # Title optimization (20 points)
        if title and len(title) >= 30 and len(title) <= 60:
            score += 15
        if keywords and any(keyword.lower() in title.lower() for keyword in keywords):
            score += 5

        # Content length (15 points)
        word_count = len(content.split())
        if word_count >= 300:
            score += 10
        if word_count >= 1000:
            score += 5

        # Keyword usage (25 points)
        if keywords:
            content_lower = content.lower()
            keyword_mentions = sum(content_lower.count(kw.lower()) for kw in keywords)
            content_length = len(content.split())

            if content_length > 0:
                keyword_density = keyword_mentions / content_length
                if 0.01 <= keyword_density <= 0.03:  # 1-3% density
                    score += 25
                elif keyword_density > 0:
                    score += 15

        # Structure analysis (20 points)
        if re.search(r"^#{1,6}\s+", content, re.MULTILINE):  # Has headers
            score += 10
        if re.search(r"^\*|\d+\.", content, re.MULTILINE):  # Has lists
            score += 10

        # Meta elements (20 points)
        # This would be checked when meta description is provided
        score += 20  # Assume basic meta optimization

        final_score = min(score, max_score)
        self.logger.debug(f"SEO analysis completed: {final_score}/{max_score} score")
        return final_score
