import textstat
import re
from typing import Dict, List
from config.logging_config import get_logger


class ContentTools:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.logger.info("Content Tools initialized")

    def calculate_readability(self, text: str) -> float:
        """Calculate Flesch Reading Ease score"""
        try:
            self.logger.debug(f"Calculating readability for {len(text)} characters")
            score = textstat.flesch_reading_ease(text)
            self.logger.debug(f"Readability score: {score}")
            return score
        except Exception as e:
            self.logger.warning(
                f"Readability calculation failed: {e}, using default score"
            )
            return 60.0  # Default moderate readability

    def analyze_readability(self, text: str) -> Dict[str, any]:
        """Comprehensive readability analysis"""
        self.logger.debug(
            f"Performing comprehensive readability analysis for {len(text)} characters"
        )

        try:
            analysis = {
                "flesch_reading_ease": textstat.flesch_reading_ease(text),
                "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
                "gunning_fog": textstat.gunning_fog(text),
                "average_sentence_length": textstat.avg_sentence_length(text),
                "syllable_count": textstat.syllable_count(text),
                "word_count": len(text.split()),
            }
            self.logger.debug(
                f"Readability analysis completed: {analysis['word_count']} words, {analysis['flesch_reading_ease']:.1f} Flesch score"
            )
            return analysis
        except Exception as e:
            self.logger.error(f"Readability analysis failed: {e}", exc_info=True)
            return {
                "flesch_reading_ease": 60.0,
                "flesch_kincaid_grade": 8.0,
                "gunning_fog": 10.0,
                "average_sentence_length": 15.0,
                "syllable_count": 0,
                "word_count": len(text.split()),
            }

    def check_grammar_basic(self, text: str) -> List[str]:
        """Basic grammar and style checks"""
        self.logger.debug(f"Performing basic grammar check for {len(text)} characters")
        issues = []

        # Check for common issues
        if re.search(r"\s{2,}", text):
            issues.append("Multiple consecutive spaces found")

        if re.search(r"[.!?]{2,}", text):
            issues.append("Multiple consecutive punctuation marks")

        # Check sentence length
        sentences = re.split(r"[.!?]+", text)
        long_sentences = [s for s in sentences if len(s.split()) > 25]
        if long_sentences:
            issues.append(f"Found {len(long_sentences)} sentences over 25 words")

        # Check paragraph length
        paragraphs = text.split("\n\n")
        long_paragraphs = [p for p in paragraphs if len(p.split()) > 150]
        if long_paragraphs:
            issues.append(f"Found {len(long_paragraphs)} paragraphs over 150 words")

        self.logger.debug(f"Grammar check completed: {len(issues)} issues found")
        return issues
