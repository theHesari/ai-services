from ..memory.content_history import ContentHistory
from ..memory.user_preferences import UserPreferences
from ..memory.brand_guidelines import BrandGuidelines
from typing import Dict, Any, List
from config.logging_config import get_logger, log_performance
import time


class FeedbackLoop:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.content_history = ContentHistory()
        self.user_preferences = UserPreferences()
        self.brand_guidelines = BrandGuidelines()
        self.logger.info("Feedback Loop initialized")

    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze content patterns to improve future content"""
        start_time = time.time()

        try:
            self.logger.info("Starting pattern analysis...")

            successful_content = self.content_history.get_successful_content()
            metrics = self.content_history.get_performance_metrics()

            self.logger.info(
                f"Analyzing {len(successful_content)} successful content pieces"
            )

            patterns = {
                "successful_topics": self._extract_successful_topics(
                    successful_content
                ),
                "preferred_tones": self._extract_preferred_tones(successful_content),
                "optimal_length": self._extract_optimal_length(successful_content),
                "performance_trends": metrics,
                "common_issues": self._extract_common_issues(),
                "improvement_suggestions": self._generate_improvement_suggestions(
                    metrics
                ),
            }

            analysis_time = time.time() - start_time
            log_performance(
                "Pattern Analysis",
                analysis_time,
                details=f"Analyzed {len(successful_content)} content pieces",
            )
            self.logger.info(f"✅ Pattern analysis completed in {analysis_time:.2f}s")

            return patterns

        except Exception as e:
            analysis_time = time.time() - start_time
            self.logger.error(
                f"❌ Pattern analysis failed after {analysis_time:.2f}s: {e}",
                exc_info=True,
            )
            raise

    def _extract_successful_topics(self, successful_content: List[Dict]) -> List[str]:
        """Extract topics from successful content"""
        self.logger.debug(
            f"Extracting topics from {len(successful_content)} successful content pieces"
        )

        topics = []
        for content in successful_content:
            topic = content["request"]["topic"]
            topics.append(topic)

        unique_topics = list(set(topics))
        self.logger.debug(f"Extracted {len(unique_topics)} unique topics")

        # Could use NLP to extract common themes
        return unique_topics

    def _extract_preferred_tones(
        self, successful_content: List[Dict]
    ) -> Dict[str, int]:
        """Extract preferred tones from successful content"""
        self.logger.debug("Extracting preferred tones from successful content")

        tone_counts = {}
        for content in successful_content:
            tone = content["request"].get("tone", "professional")
            tone_counts[tone] = tone_counts.get(tone, 0) + 1

        self.logger.debug(f"Tone distribution: {tone_counts}")
        return tone_counts

    def _extract_optimal_length(self, successful_content: List[Dict]) -> Dict[str, Any]:
        """Extract optimal content length patterns"""
        self.logger.debug("Analyzing optimal content length patterns")

        lengths = [content["draft"]["word_count"] for content in successful_content]

        if lengths:
            avg_length = sum(lengths) / len(lengths)
            result = {
                "average": avg_length,
                "min": min(lengths),
                "max": max(lengths),
                "recommendation": "medium" if avg_length < 1000 else "long",
            }
            self.logger.debug(
                f"Length analysis: avg={avg_length:.0f}, min={min(lengths)}, max={max(lengths)}"
            )
            return result

        self.logger.debug("No content lengths available, using default recommendation")
        return {"recommendation": "medium"}

    def _extract_common_issues(self) -> List[str]:
        """Extract common issues from quality reports"""
        self.logger.debug("Extracting common issues from quality reports")

        all_issues = []
        for session in self.content_history.history:
            all_issues.extend(session["quality_report"]["issues"])

        # Count frequency of issues
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

        # Return most common issues
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        top_issues = [issue for issue, count in sorted_issues[:5]]

        self.logger.debug(f"Found {len(all_issues)} total issues, top 5: {top_issues}")
        return top_issues

    def _generate_improvement_suggestions(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions based on metrics"""
        self.logger.debug("Generating improvement suggestions based on metrics")

        suggestions = []

        approval_rate = metrics.get("approval_rate", 0)
        avg_quality = metrics.get("average_quality_score", 0)

        if approval_rate < 0.8:
            suggestions.append(
                "Focus on improving content quality - approval rate is below 80%"
            )
            self.logger.debug(f"Low approval rate detected: {approval_rate:.2%}")

        if avg_quality < 75:
            suggestions.append("Work on improving overall content quality scores")
            self.logger.debug(f"Low average quality score detected: {avg_quality}")

        self.logger.debug(f"Generated {len(suggestions)} improvement suggestions")
        return suggestions
