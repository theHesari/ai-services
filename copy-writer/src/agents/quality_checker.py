from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from ..models.content_models import ContentDraft, QualityReport
from ..tools.content_tools import ContentTools
from ..tools.seo_tools import SEOAnalyzer
from typing import List
import time
from config.logging_config import get_logger, log_agent_action, log_performance


class QualityChecker:
    def __init__(self, llm: ChatOpenAI):
        self.logger = get_logger(__name__)
        self.llm = llm
        self.content_tools = ContentTools()
        self.seo_analyzer = SEOAnalyzer()
        self.logger.info("Quality Checker agent initialized")

        self.quality_prompt = PromptTemplate(
            template="""
            You are a content quality expert. Analyze this content and provide a comprehensive quality assessment.
            
            CONTENT TO ANALYZE:
            Title: {title}
            Word Count: {word_count}
            Target Keywords: {target_keywords}
            
            Content:
            {content}
            
            QUALITY CRITERIA:
            1. Content Quality & Value (Does it provide real value? Is it engaging?)
            2. SEO Optimization (Proper keyword usage, structure, meta elements)
            3. Readability (Clear, scannable, appropriate for audience)
            4. Brand Voice Consistency (Tone, messaging alignment)
            5. Technical Issues (Grammar, spelling, formatting)
            
            CURRENT METRICS:
            - Readability Score: {readability_score}
            - SEO Score: {seo_score}
            
            Provide assessment in this format:
            OVERALL_SCORE: [0-100]
            
            SCORES:
            Content Quality: [0-100]
            SEO Optimization: [0-100] 
            Readability: [0-100]
            Brand Voice: [0-100]
            Technical Quality: [0-100]
            
            ISSUES:
            - [Issue 1]
            - [Issue 2]
            ...
            
            SUGGESTIONS:
            - [Suggestion 1]
            - [Suggestion 2]
            ...
            
            APPROVED: [YES/NO]
            """,
            input_variables=[
                "title",
                "word_count",
                "target_keywords",
                "content",
                "readability_score",
                "seo_score",
            ],
        )

    def check_quality(self, draft: ContentDraft) -> QualityReport:
        """Perform comprehensive quality check on content draft"""
        start_time = time.time()

        try:
            self.logger.info(f"Starting quality check for draft: {draft.title}")
            log_agent_action(
                "QualityChecker",
                "Check Quality",
                draft.request_id,
                f"Title: {draft.title}",
            )

            # Calculate SEO score
            self.logger.debug("Calculating SEO score...")
            seo_start = time.time()
            seo_score = self.seo_analyzer.analyze_content(
                draft.content,
                draft.title,
                keywords=getattr(draft, "target_keywords", []),
            )
            seo_time = time.time() - seo_start
            log_performance("SEO Analysis", seo_time, draft.request_id)

            self.logger.info(f"SEO score calculated: {seo_score}")

            # Run quality analysis with LLM
            self.logger.info("Running LLM quality analysis...")
            prompt = self.quality_prompt.format(
                title=draft.title,
                word_count=draft.word_count,
                target_keywords=", ".join(draft.tags or []),
                content=draft.content,
                readability_score=draft.readability_score or 0,
                seo_score=seo_score,
            )

            llm_start = time.time()
            response = self.llm.invoke(prompt)
            llm_time = time.time() - llm_start
            log_performance("LLM Quality Analysis", llm_time, draft.request_id)

            self.logger.info("LLM quality analysis completed, parsing results...")
            quality_data = self._parse_quality_response(response.content)

            # Create quality report
            report = QualityReport(
                request_id=draft.request_id,
                overall_score=quality_data.get("overall_score", 75),
                readability_score=draft.readability_score or 0,
                seo_score=seo_score,
                brand_voice_score=quality_data.get("brand_voice_score", 80),
                issues=quality_data.get("issues", []),
                suggestions=quality_data.get("suggestions", []),
                approved=quality_data.get("approved", False),
            )

            total_time = time.time() - start_time
            log_performance(
                "Quality Check",
                total_time,
                draft.request_id,
                f"Score: {report.overall_score}, Approved: {report.approved}",
            )
            self.logger.info(
                f"✅ Quality check completed for {draft.request_id} in {total_time:.2f}s - Score: {report.overall_score}, Approved: {report.approved}"
            )

            return report

        except Exception as e:
            total_time = time.time() - start_time
            self.logger.error(
                f"❌ Quality check failed for {draft.request_id} after {total_time:.2f}s: {e}",
                exc_info=True,
            )
            raise

    def _parse_quality_response(self, response: str) -> dict:
        """Parse LLM quality assessment response"""
        quality_data = {
            "overall_score": 75,  # Default fallback
            "content_quality_score": 75,
            "seo_score": 75,
            "readability_score": 75,
            "brand_voice_score": 75,
            "technical_quality_score": 75,
            "issues": [],
            "suggestions": [],
            "approved": False,
        }

        current_section = None
        lines = response.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Parse overall score
            if line.startswith("OVERALL_SCORE:"):
                score_text = line.replace("OVERALL_SCORE:", "").strip()
                quality_data["overall_score"] = self._extract_score(score_text)

            # Parse individual scores
            elif line.startswith("Content Quality:"):
                quality_data["content_quality_score"] = self._extract_score(line)
            elif line.startswith("SEO Optimization:"):
                quality_data["seo_score"] = self._extract_score(line)
            elif line.startswith("Readability:"):
                quality_data["readability_score"] = self._extract_score(line)
            elif line.startswith("Brand Voice:"):
                quality_data["brand_voice_score"] = self._extract_score(line)
            elif line.startswith("Technical Quality:"):
                quality_data["technical_quality_score"] = self._extract_score(line)

            # Parse sections
            elif line == "ISSUES:":
                current_section = "issues"
            elif line == "SUGGESTIONS:":
                current_section = "suggestions"
            elif line.startswith("APPROVED:"):
                approved_text = line.replace("APPROVED:", "").strip().upper()
                quality_data["approved"] = approved_text in [
                    "YES",
                    "TRUE",
                    "1",
                    "APPROVED",
                ]

            # Parse list items
            elif current_section and line.startswith("- "):
                item = line[2:].strip()  # Remove '- ' prefix
                if current_section == "issues":
                    quality_data["issues"].append(item)
                elif current_section == "suggestions":
                    quality_data["suggestions"].append(item)

        return quality_data

    def _extract_score(self, text: str) -> float:
        """Extract numeric score from text"""
        import re

        # Look for numbers in the text
        numbers = re.findall(r"\d+(?:\.\d+)?", text)
        if numbers:
            score = float(numbers[0])
            # Ensure score is within valid range
            return max(0, min(100, score))
        return 75.0  # Default fallback


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from src.models.content_models import ContentPlan
    from src.agents.content_writer import ContentWriter
    from src.agents.quality_checker import QualityChecker

    load_dotenv()

    llm_config = {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_BASE_URL"),
        "model": os.getenv("OPENAI_MODEL"),
    }
    writer = ContentWriter(llm=ChatOpenAI(**llm_config))
    quality_checker = QualityChecker(llm=ChatOpenAI(**llm_config))

    plan = ContentPlan(
        request_id="123",
        title="iPhone 17 Air 512GB Color - Lavender",
        outline=["Outline 1", "Outline 2", "Outline 3"],
        target_keywords=["iPhone 17", "Air", "512GB", "Lavender"],
        word_count_target=800,
        tone="premium and aspirational",
        key_messages=["Key message 1", "Key message 2", "Key message 3"],
    )
    draft = writer.write_content(plan)
    report = quality_checker.check_quality(draft)
    print(report)
