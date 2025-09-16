"""
Competitor Analysis Tool for Content Writer Agent
Analyzes competitor content to inform content strategy
"""

from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from config.logging_config import get_logger


class CompetitorAnalyzer:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.logger.info("Competitor Analyzer initialized")

    def analyze_competitor_content(self, url: str) -> Dict[str, Any]:
        """Analyze competitor content from URL"""
        self.logger.info(f"Starting competitor analysis for URL: {url}")

        try:
            # Fetch content
            self.logger.debug("Fetching competitor content...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Parse content
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract key elements
            title = soup.find("title")
            title_text = title.get_text().strip() if title else "No title found"

            # Extract main content (simplified)
            main_content = (
                soup.find("main")
                or soup.find("article")
                or soup.find("div", class_="content")
            )
            content_text = (
                main_content.get_text().strip() if main_content else "No content found"
            )

            # Basic analysis
            word_count = len(content_text.split())

            analysis = {
                "url": url,
                "title": title_text,
                "word_count": word_count,
                "content_preview": (
                    content_text[:500] + "..."
                    if len(content_text) > 500
                    else content_text
                ),
                "status": "success",
            }

            self.logger.info(
                f"Competitor analysis completed: {word_count} words, title: {title_text[:50]}..."
            )
            return analysis

        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch competitor content from {url}: {e}")
            return {"url": url, "status": "error", "error": str(e)}
        except Exception as e:
            self.logger.error(
                f"Unexpected error during competitor analysis: {e}", exc_info=True
            )
            return {"url": url, "status": "error", "error": str(e)}

    def analyze_multiple_competitors(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Analyze multiple competitor URLs"""
        self.logger.info(f"Starting analysis of {len(urls)} competitor URLs")

        results = []
        for url in urls:
            result = self.analyze_competitor_content(url)
            results.append(result)

        successful_analyses = len([r for r in results if r.get("status") == "success"])
        self.logger.info(
            f"Competitor analysis completed: {successful_analyses}/{len(urls)} successful"
        )

        return results

    def extract_content_insights(
        self, analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract insights from competitor analyses"""
        self.logger.info("Extracting insights from competitor analyses")

        successful_analyses = [a for a in analyses if a.get("status") == "success"]

        if not successful_analyses:
            self.logger.warning(
                "No successful competitor analyses to extract insights from"
            )
            return {"insights": [], "summary": "No data available"}

        # Basic insights
        avg_word_count = sum(a.get("word_count", 0) for a in successful_analyses) / len(
            successful_analyses
        )
        titles = [a.get("title", "") for a in successful_analyses]

        insights = {
            "average_word_count": avg_word_count,
            "title_patterns": titles,
            "competitor_count": len(successful_analyses),
            "insights": [
                f"Average content length: {avg_word_count:.0f} words",
                f"Analyzed {len(successful_analyses)} competitor pages",
            ],
        }

        self.logger.info(
            f"Insights extracted: avg {avg_word_count:.0f} words across {len(successful_analyses)} competitors"
        )
        return insights
